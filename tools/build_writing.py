#!/usr/bin/env python3
"""Builds the /writing/ section into dist/.

Each article is one HTML fragment in writing/ that starts with a JSON header in an
HTML comment:

    <!--
    {"slug": "file-uploads", "lang": "en", "title": "...", "description": "...",
     "date": "2026-10-27", "status": "draft", "topic": "Security", "pair": "file-uploads"}
    -->
    <p>Article body…</p>

English articles are served at /writing/<slug>/, Arabic ones at /writing/ar/<slug>/.
Articles with the same "pair" link to each other as translations.
Drafts are only built when PREVIEW=1, so they never reach the live site by accident.

Usage: python3 tools/build_writing.py dist
"""
import html
import json
import os
import re
import sys
from datetime import date

SITE = 'https://mohamedsharaf.com'
DIST = sys.argv[1]
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PREVIEW = os.environ.get('PREVIEW') == '1'

TEXT = {
    'en': dict(dir='ltr', writing='Writing', home='Home', menu='Menu', hello='Say hello', other='عربي', other_lang='ar',
               index_title='Writing', index_intro='Notes on security, infrastructure, software and AI. Written in plain words, from three decades of doing the work.',
               min_read='min read', back='All writing', cta_title='Want a second pair of eyes?',
               cta_text='If something here sounds like your system, write to me. I read everything.',
               cta_link='Say hello', draft='Draft: not published yet', empty='The first articles are on their way.',
               new_heading='New', archive_heading='From the archive', archive_intro='Notes from my old blog on mohamedsharaf.net (2010–2023), rewritten and checked. Some are dated; the dates tell you how much.',
               months=['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December']),
    'ar': dict(dir='rtl', writing='كتابات', home='الرئيسية', menu='القائمة', hello='قل مرحبًا', other='English', other_lang='en',
               index_title='كتابات', index_intro='ملاحظات عن الأمن والبنية التحتية والبرمجيات والذكاء الاصطناعي، بكلام واضح، من ثلاثة عقود من العمل.',
               min_read='دقائق قراءة', back='كل الكتابات', cta_title='تحتاج إلى نظرة ثانية؟',
               cta_text='إذا بدا لك شيء هنا مثل نظامك، اكتب لي. أقرأ كل شيء.',
               cta_link='تواصل معي', draft='مسودة: لم تُنشر بعد', empty='أول المقالات في الطريق.',
               new_heading='جديد', archive_heading='من الأرشيف', archive_intro='ملاحظات من مدونتي القديمة على mohamedsharaf.net (2010–2023)، أُعيدت كتابتها ومراجعتها. بعضها قديم، والتاريخ يوضح كم.',
               months=['يناير', 'فبراير', 'مارس', 'أبريل', 'مايو', 'يونيو', 'يوليو', 'أغسطس', 'سبتمبر', 'أكتوبر', 'نوفمبر', 'ديسمبر']),
}

CSS = """
@font-face{font-family:Manrope;src:url('/assets/manrope-latin.woff2') format('woff2');font-weight:200 800;font-display:swap}
@font-face{font-family:'IBM Plex Sans Arabic';src:url('/assets/plex-arabic-400.woff2') format('woff2');font-weight:400;font-display:swap;unicode-range:U+060C,U+061B,U+061F,U+0621-063A,U+0640-0652,U+0660-0669,U+0670,U+200C-200F}
@font-face{font-family:'IBM Plex Sans Arabic';src:url('/assets/plex-arabic-600.woff2') format('woff2');font-weight:600;font-display:swap;unicode-range:U+060C,U+061B,U+061F,U+0621-063A,U+0640-0652,U+0660-0669,U+0670,U+200C-200F}
:root{--paper:#eeeae2;--paper-card:#f6f4ee;--ink:#242624;--muted:#5f6059;--orange:#e85532;--orange-ink:#ad3a1c;--line:#cecdc4;--code-bg:#242a25;--code-text:#d6e6c4;--mono:'SFMono-Regular',Consolas,'Liberation Mono',monospace;--sans:Manrope,'IBM Plex Sans Arabic','Segoe UI',Tahoma,sans-serif}
*{box-sizing:border-box}
html{scroll-behavior:smooth}
body{margin:0;background:var(--paper);color:var(--ink);font-family:var(--sans);-webkit-font-smoothing:antialiased}
a{color:inherit}
a:focus-visible{outline:3px solid var(--orange);outline-offset:4px}
.shell{width:min(1180px,calc(100% - 40px));margin:auto}
.header{display:flex;justify-content:space-between;align-items:center;gap:18px;height:86px;border-bottom:1px solid var(--line)}
.brand{display:flex;align-items:center;gap:12px;font-size:15px;font-weight:750;letter-spacing:-.6px;text-decoration:none;white-space:nowrap}
.brand i{width:7px;height:7px;background:var(--orange)}
.sym{display:grid;grid-template-columns:repeat(2,7px);gap:3px;transform:rotate(-7deg)}
.sym i:last-child{opacity:.35}
.nav{display:flex;gap:18px;align-items:center;font-size:13px;font-weight:600}
.nav a{text-decoration:none}
.nav .lang{border:1px solid var(--line);padding:7px 10px}
.nav .hello{background:var(--ink);color:var(--paper);padding:9px 13px}
.menu{display:none;position:relative}
.menu-button{list-style:none;display:flex;align-items:center;gap:9px;min-height:40px;padding:0 13px;border:1px solid var(--ink);font-size:13px;font-weight:600;cursor:pointer;user-select:none;-webkit-user-select:none}
.menu-button::-webkit-details-marker{display:none}
.menu-button:focus-visible{outline:3px solid var(--orange);outline-offset:4px}
.menu-icon{display:grid;gap:3px;width:14px}
.menu-icon i{display:block;height:2px;background:currentColor}
.menu[open] .menu-button{background:var(--ink);color:var(--paper)}
.menu[open] .menu-icon i:nth-child(1){transform:translateY(5px) rotate(45deg)}
.menu[open] .menu-icon i:nth-child(2){opacity:0}
.menu[open] .menu-icon i:nth-child(3){transform:translateY(-5px) rotate(-45deg)}
.menu-panel{position:absolute;inset-inline-end:0;top:calc(100% + 10px);z-index:60;width:min(280px,calc(100vw - 40px));background:var(--paper-card);border:1px solid var(--ink);box-shadow:6px 6px 0 rgba(36,38,36,.12);display:flex;flex-direction:column}
.menu-panel a{padding:15px 18px;font-size:15px;font-weight:600;text-decoration:none;border-bottom:1px solid var(--line)}
.menu-panel .menu-cta{background:var(--ink);color:var(--paper);border-bottom:0}
.kicker{font:12px var(--mono);letter-spacing:.08em;text-transform:uppercase;color:var(--orange-ink)}
.article{max-width:720px;margin:0 auto;padding:64px 0 40px}
.article h1{font-size:clamp(34px,6vw,54px);line-height:1.12;letter-spacing:-.04em;font-weight:700;margin:16px 0 16px}
.lead{font-size:19px;line-height:1.7;color:var(--muted);margin:0 0 18px}
.meta{font:12px var(--mono);letter-spacing:.06em;color:var(--muted);padding-bottom:26px;border-bottom:1px solid var(--line);margin-bottom:34px}
.draft{display:inline-block;background:#f5e7df;color:var(--orange-ink);font:600 12px var(--mono);padding:6px 10px;margin-bottom:18px}
.body{font-size:17px;line-height:1.85}
.body h2{font-size:26px;letter-spacing:-.02em;line-height:1.3;margin:46px 0 12px}
.body h3{font-size:19px;margin:30px 0 8px}
.body p{margin:0 0 18px}
.body ul,.body ol{padding-inline-start:22px;margin:0 0 20px}
.body li{margin-bottom:8px}
.body a{color:var(--orange-ink);text-underline-offset:3px}
.body strong{font-weight:700}
.body code{font:15px var(--mono);background:#e4e0d5;padding:2px 5px;border-radius:3px;unicode-bidi:isolate;direction:ltr}
.body pre{direction:ltr;text-align:left;background:var(--code-bg);color:var(--code-text);padding:18px 20px;overflow:auto;font:14px/1.7 var(--mono);margin:0 0 22px}
.body pre code{background:none;padding:0;color:inherit;font:inherit}
.body blockquote{margin:0 0 22px;padding:4px 20px;border-inline-start:3px solid var(--orange);color:var(--muted)}
.body .note{background:var(--paper-card);border:1px solid var(--line);padding:18px 20px;margin:0 0 22px;font-size:16px}
.archived{background:var(--paper-card);border:1px solid var(--line);border-inline-start:3px solid var(--orange);padding:12px 16px;margin:-8px 0 30px;font-size:14px;color:var(--muted)}
.cta{max-width:720px;margin:10px auto 70px;padding:28px;background:var(--ink);color:var(--paper);display:flex;justify-content:space-between;align-items:center;gap:24px;flex-wrap:wrap}
.cta h2{margin:0 0 6px;font-size:22px}
.cta p{margin:0;color:#c9c6bd;font-size:15px}
.cta a{background:#c9441f;color:#fff;padding:12px 18px;font-weight:600;text-decoration:none;white-space:nowrap}
.index{max-width:820px;margin:0 auto;padding:64px 0 80px}
.index h1{font-size:clamp(40px,7vw,64px);letter-spacing:-.05em;margin:14px 0 14px}
.index ol{list-style:none;padding:0;margin:18px 0 0;border-top:1px solid var(--line)}
.index .group{font-size:15px;font-family:var(--mono);font-weight:600;letter-spacing:.08em;text-transform:uppercase;color:var(--orange-ink);margin:48px 0 0}
.index .group-intro{color:var(--muted);line-height:1.7;margin:8px 0 0;font-size:15px}
.index ol.archive li{padding:16px 0}
.index ol.archive h2{font-size:19px}
[dir=rtl] .index .group{font-family:var(--sans);letter-spacing:0;font-size:16px}
.index li{padding:24px 0;border-bottom:1px solid var(--line)}
.index li a{text-decoration:none;display:block}
.index li h2{font-size:24px;letter-spacing:-.02em;margin:8px 0 6px}
.index li p{margin:0;color:var(--muted);line-height:1.7}
.footer{border-top:1px solid var(--line);padding:24px 0 30px;display:flex;justify-content:space-between;gap:16px;flex-wrap:wrap;font-size:13px;color:var(--muted)}
.footer a{text-decoration:none}
[dir=rtl] .body,[dir=rtl] .lead{font-size:18px}
[dir=rtl] .article h1,[dir=rtl] .index h1,[dir=rtl] .body h2,[dir=rtl] .index li h2{letter-spacing:0;line-height:1.4}
[dir=rtl] .kicker,[dir=rtl] .meta,[dir=rtl] .draft{font-family:var(--sans);letter-spacing:0;font-size:13px}
@media(max-width:600px){.nav .hide,.nav .hello{display:none}.nav{margin-inline-start:auto}.header{gap:10px}.menu{display:block}.article,.index{padding-top:40px}.body{font-size:16.5px}.cta{padding:22px}}
"""


def read_articles():
    out = []
    folder = os.path.join(ROOT, 'writing')
    for name in sorted(os.listdir(folder)) if os.path.isdir(folder) else []:
        if not name.endswith('.html'):
            continue
        raw = open(os.path.join(folder, name), encoding='utf-8').read()
        m = re.match(r'\s*<!--\s*(\{.*?\})\s*-->\s*', raw, re.S)
        meta = json.loads(m.group(1))
        meta['body'] = raw[m.end():].strip()
        meta['words'] = len(re.sub(r'<[^>]+>', ' ', meta['body']).split())
        if meta.get('status') == 'published' or PREVIEW:
            out.append(meta)
    return out


def url_for(a):
    return f"/writing/{a['slug']}/" if a['lang'] == 'en' else f"/writing/ar/{a['slug']}/"


def nice_date(d, lang):
    y, mo, da = map(int, d.split('-'))
    return f"{da} {TEXT[lang]['months'][mo - 1]} {y}"


def page(lang, title, description, canonical, body, head_extra='', alternates=None, other_url=None, og_image=None):
    t = TEXT[lang]
    alt = ''.join(f'<link rel="alternate" hreflang="{l}" href="{SITE}{u}">\n  ' for l, u in (alternates or {}).items())
    other = other_url or ('/writing/ar/' if lang == 'en' else '/writing/')
    # Fetch the fonts early so big headings don't jump when they arrive (Latin always, Arabic on Arabic pages)
    preload = '<link rel="preload" href="/assets/manrope-latin.woff2" as="font" type="font/woff2" crossorigin>\n  '
    if lang == 'ar':
        preload += ''.join(f'<link rel="preload" href="/assets/plex-arabic-{w}.woff2" as="font" type="font/woff2" crossorigin>\n  ' for w in (400, 600))
    og_image = og_image or f"{SITE}/assets/og-{'en' if lang == 'en' else 'ar'}.jpg"
    return f"""<!doctype html>
<html lang="{lang}" dir="{t['dir']}">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="theme-color" content="#eeeae2">
  <title>{html.escape(title)} — {'Mohamed Sharaf' if lang == 'en' else 'محمد شرف'}</title>
  <meta name="description" content="{html.escape(description)}">
  <link rel="canonical" href="{SITE}{canonical}">
  {alt}<meta property="og:title" content="{html.escape(title)}">
  <meta property="og:description" content="{html.escape(description)}">
  <meta property="og:type" content="article">
  <meta property="og:url" content="{SITE}{canonical}">
  <meta property="og:site_name" content="Mohamed Sharaf">
  <meta property="og:image" content="{og_image}">
  <meta name="twitter:card" content="summary_large_image">
  <link rel="icon" href="/favicon.svg" type="image/svg+xml">
  <link rel="apple-touch-icon" href="/apple-touch-icon.png">
  {preload}{head_extra}<style>{CSS}</style>
</head>
<body>
  <header class="header shell">
    <a class="brand" href="{'/' if lang == 'en' else '/ar'}"><span class="sym" aria-hidden="true"><i></i><i></i><i></i><i></i></span>{'Mohamed Sharaf' if lang == 'en' else 'محمد شرف'}</a>
    <nav class="nav" aria-label="{t['writing']}">
      <a class="hide" href="{'/writing/' if lang == 'en' else '/writing/ar/'}">{t['writing']}</a>
      <a class="lang" href="{other}" lang="{t['other_lang']}" hreflang="{t['other_lang']}">{t['other']}</a>
      <a class="hello" href="{'/#contact' if lang == 'en' else '/ar#contact'}">{t['hello']}</a>
    </nav>
    <details class="menu">
      <summary class="menu-button"><span class="menu-icon" aria-hidden="true"><i></i><i></i><i></i></span>{t['menu']}</summary>
      <nav class="menu-panel" aria-label="{t['menu']}">
        <a href="{'/' if lang == 'en' else '/ar'}">{t['home']}</a>
        <a href="{'/writing/' if lang == 'en' else '/writing/ar/'}">{t['writing']}</a>
        <a class="menu-cta" href="{'/#contact' if lang == 'en' else '/ar#contact'}">{t['hello']}</a>
      </nav>
    </details>
  </header>
  <main class="shell">
{body}
  </main>
  <footer class="footer shell">
    <span>© {date.today().year} {'Mohamed Sharaf' if lang == 'en' else 'محمد شرف'}</span>
    <a href="{'/writing/' if lang == 'en' else '/writing/ar/'}">{t['back']} {'→' if lang == 'en' else '←'}</a>
  </footer>
</body>
</html>
"""


def article_page(a, pair):
    t = TEXT[a['lang']]
    canonical = url_for(a)
    alternates = {a['lang']: canonical}
    if pair:
        alternates[pair['lang']] = url_for(pair)
    minutes = max(1, round(a['words'] / 200))
    ld = {
        '@context': 'https://schema.org', '@type': 'BlogPosting',
        'headline': a['title'], 'description': a['description'], 'inLanguage': a['lang'],
        'datePublished': a['date'], 'dateModified': a.get('updated', a['date']),
        'url': SITE + canonical, 'mainEntityOfPage': SITE + canonical,
        'image': f"{SITE}/assets/og-{'en' if a['lang'] == 'en' else 'ar'}.jpg",
        'author': {'@type': 'Person', '@id': f'{SITE}/#person', 'name': 'Mohamed Sharaf', 'url': SITE + '/'},
        'publisher': {'@type': 'Person', '@id': f'{SITE}/#person', 'name': 'Mohamed Sharaf'},
        'isPartOf': {'@id': f'{SITE}/#site'},
    }
    head = f'<script type="application/ld+json">{json.dumps(ld, ensure_ascii=False)}</script>\n  '
    if a.get('status') != 'published':
        head += '<meta name="robots" content="noindex">\n  '
    draft = f'<div class="draft">{t["draft"]}</div>' if a.get('status') != 'published' else ''
    archive = f'<p class="archived">{html.escape(a["archive_note"])}</p>\n      ' if a.get('archive_note') else ''
    body = f"""    <article class="article">
      {draft}<div class="kicker">{html.escape(a.get('topic', ''))}</div>
      <h1>{html.escape(a['title'])}</h1>
      <p class="lead">{html.escape(a['description'])}</p>
      <div class="meta"><time datetime="{a['date']}">{nice_date(a['date'], a['lang'])}</time> · {minutes} {t['min_read']}</div>
      {archive}<div class="body">
{a['body']}
      </div>
    </article>
    <aside class="cta"><div><h2>{t['cta_title']}</h2><p>{t['cta_text']}</p></div><a href="{'/#contact' if a['lang'] == 'en' else '/ar#contact'}">{t['cta_link']}</a></aside>"""
    other = url_for(pair) if pair else other_index(a['lang'])
    return page(a['lang'], a['title'], a['description'], canonical, body, head, alternates, other)


def index_page(lang, items):
    t = TEXT[lang]
    canonical = '/writing/' if lang == 'en' else '/writing/ar/'
    def rows(group):
        return ''.join(
            f"""      <li><a href="{url_for(a)}"><span class="kicker">{html.escape(a.get('topic', ''))} · {nice_date(a['date'], lang)}</span><h2>{html.escape(a['title'])}</h2><p>{html.escape(a['description'])}</p></a></li>\n"""
            for a in group)
    new = [a for a in items if not a.get('archive')]
    old = [a for a in items if a.get('archive')]
    sections = ''
    if new:
        sections += f'      <h2 class="group">{t["new_heading"]}</h2>\n      <ol>\n{rows(new)}      </ol>\n'
    if old:
        sections += f'      <h2 class="group">{t["archive_heading"]}</h2>\n      <p class="group-intro">{t["archive_intro"]}</p>\n      <ol class="archive">\n{rows(old)}      </ol>\n'
    body = f"""    <section class="index">
      <div class="kicker">{'Mohamed Sharaf' if lang == 'en' else 'محمد شرف'}</div>
      <h1>{t['index_title']}</h1>
      <p class="lead">{t['index_intro']}</p>
{sections}    </section>"""
    return page(lang, t['index_title'], t['index_intro'], canonical, body,
                alternates={l: INDEX[l] for l in LANGS_WITH_ITEMS},
                other_url=other_index(lang))


def write(path, text):
    full = os.path.join(DIST, path.strip('/'), 'index.html')
    os.makedirs(os.path.dirname(full), exist_ok=True)
    open(full, 'w', encoding='utf-8').write(text)


INDEX = {'en': '/writing/', 'ar': '/writing/ar/'}


def other_index(lang):
    other = 'ar' if lang == 'en' else 'en'
    return INDEX[other] if other in LANGS_WITH_ITEMS else ('/ar' if other == 'ar' else '/')


articles = read_articles()
LANGS_WITH_ITEMS = {a['lang'] for a in articles}

# Links to articles that are not built (drafts in a normal build) become plain text,
# so a published page never links to a page that doesn't exist yet.
BUILT_URLS = {url_for(a) for a in articles}


def unlink_missing(body):
    def fix(m):
        href = m.group(1)
        if href.startswith('/writing/') and href not in BUILT_URLS:
            return m.group(2)
        return m.group(0)
    return re.sub(r'<a href="([^"]+)">(.*?)</a>', fix, body, flags=re.S)


for a in articles:
    a['body'] = unlink_missing(a['body'])
    # Headings must not skip a level after the page's h1: short notes that only use h3 get h2
    if '<h2' not in a['body']:
        a['body'] = a['body'].replace('<h3>', '<h2>').replace('</h3>', '</h2>')
by_pair = {}
for a in articles:
    by_pair.setdefault(a.get('pair') or a['slug'], []).append(a)
for a in articles:
    pair = next((b for b in by_pair[a.get('pair') or a['slug']] if b is not a), None)
    write(url_for(a), article_page(a, pair))
# Index pages only exist once a language has something to list
index_urls = []
for lang in ('en', 'ar'):
    items = sorted((a for a in articles if a['lang'] == lang), key=lambda a: a['date'], reverse=True)
    if items:
        url = '/writing/' if lang == 'en' else '/writing/ar/'
        write(url, index_page(lang, items))
        index_urls.append(url)

# Add the writing pages and published articles to the sitemap (never drafts)
published = [a for a in articles if a.get('status') == 'published']
public_urls = [u for u in index_urls if any(a['lang'] == ('en' if u == '/writing/' else 'ar') for a in published)]
extra = ''.join(f"  <url>\n    <loc>{SITE}{u}</loc>\n  </url>\n" for u in public_urls + [url_for(a) for a in published])
if extra:
    sitemap = os.path.join(DIST, 'sitemap.xml')
    s = open(sitemap, encoding='utf-8').read().replace('</urlset>', extra + '</urlset>')
    open(sitemap, 'w', encoding='utf-8').write(s)
# Old addresses (the WordPress blog that lived on mohamedsharaf.net) forward to the nearest page.
# Restored articles come first, then legacy-redirects.txt; the first rule for a path wins.
PUBLISHED_LANGS = {a['lang'] for a in published}
PUBLISHED_URLS = {(a['lang'], a['slug']): url_for(a) for a in published}


def resolve(target):
    if target.startswith('@writing:'):
        lang = target.split(':')[1]
        return INDEX[lang] if lang in PUBLISHED_LANGS else ('/ar' if lang == 'ar' else '/')
    if target.startswith('@article:'):
        _, lang, slug = target.split(':')
        return PUBLISHED_URLS.get((lang, slug)) or resolve(f'@writing:{lang}')
    return target


rules, sources = [], set()
for a in published:
    for old in a.get('legacy_paths', []):
        rules.append((old, url_for(a)))
legacy = os.path.join(ROOT, 'legacy-redirects.txt')
for line in open(legacy, encoding='utf-8') if os.path.exists(legacy) else []:
    line = line.strip()
    if line and not line.startswith('#'):
        src, dst = line.split()
        rules.append((src, resolve(dst)))


def variants(src):
    """Other spellings of an old address that WordPress also answered: both cases of the
    percent-encoding, with and without the trailing slash, and a post's feed, AMP and comment pages."""
    if '*' in src or ':' in src or src == '/' or not src.isascii():
        return []
    cases = {re.sub(r'%[0-9a-fA-F]{2}', lambda m: m.group(0).upper(), src),
             re.sub(r'%[0-9a-fA-F]{2}', lambda m: m.group(0).lower(), src)}
    out = []
    for c in sorted(cases):
        base = c.rstrip('/') + '/'
        out += [base, base[:-1]]
        if base.count('/') == 2:  # a top-level post or page
            out += [base + 'feed/', base + 'feed', base + 'amp/', base + 'amp', base + 'comment-page-1/', base + 'comment-page-2/']
    return out


exact = [(s, d) for s, d in rules if '*' not in s]
rules = exact + [(v, d) for s, d in exact for v in variants(s)] + [(s, d) for s, d in rules if '*' in s]
lines = []
for src, dst in rules:
    if src not in sources:
        sources.add(src)
        lines.append(f'{src} {dst} 301')
# Cloudflare static assets limits (free and paid): 2,000 static + 100 dynamic rules, 1,000 characters each
dynamic = sum('*' in l or '/:' in l for l in lines)
assert len(lines) - dynamic <= 2000 and dynamic <= 100, f'_redirects over the limit: {len(lines) - dynamic} static, {dynamic} dynamic'
assert all(len(l) <= 1000 for l in lines), '_redirects rule over 1,000 characters'
if lines:
    with open(os.path.join(DIST, '_redirects'), 'a', encoding='utf-8') as f:
        f.write('\n'.join(lines) + '\n')

# Homepage links to the writing section, only for a language that has published articles
LINKS = {
    'index.html': ('en', '<a class="nav-writing" href="/writing/">Writing</a>',
                   '<a class="notes-more" href="/writing/">More writing <span aria-hidden="true">→</span></a>'),
    'ar.html': ('ar', '<a class="nav-writing" href="/writing/ar/">كتابات</a>',
                '<a class="notes-more" href="/writing/ar/">المزيد من الكتابات <span aria-hidden="true">←</span></a>'),
}
for name, (lang, nav, more) in LINKS.items():
    path = os.path.join(DIST, name)
    page_html = open(path, encoding='utf-8').read()
    show = lang in PUBLISHED_LANGS
    menu_link = nav.replace(' class="nav-writing"', '')
    page_html = (page_html.replace('<!--WRITING_NAV-->', nav if show else '')
                 .replace('<!--WRITING_MORE-->', more if show else '')
                 .replace('<!--WRITING_MENU-->', menu_link if show else ''))
    open(path, 'w', encoding='utf-8').write(page_html)
print(f"writing: {len(articles)} article(s) built ({len(published)} published), {len(lines)} redirect rules{' [PREVIEW: drafts included]' if PREVIEW else ''}")
