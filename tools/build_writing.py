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
from urllib.parse import quote

SITE = 'https://mohamedsharaf.com'
DIST = sys.argv[1]
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PREVIEW = os.environ.get('PREVIEW') == '1'

TEXT = {
    'en': dict(dir='ltr', share='Share', copy='Copy link', copied='Copied', share_native='Share…', which='Which Mohamed Sharaf?', writing='Writing', topics='Topics', all_topics='All', topic_intro='Everything I’ve written on {topic}, newest first.', home='Home', menu='Menu', hello='Say hello', other='عربي', other_lang='ar',
               index_title='Writing', index_intro='Notes on security, infrastructure, software and AI. Written in plain words, from three decades of doing the work.',
               min_read='min read', back='All writing', cta_title='Want a second pair of eyes?',
               cta_text='If something here sounds like your system, write to me. I read everything.',
               cta_link='Say hello', draft='Draft: not published yet', empty='The first articles are on their way.',
               new_heading='New', archive_heading='From the archive', archive_intro='Notes from my old blog on mohamedsharaf.net (2010–2018), rewritten and checked. Some are dated; the dates tell you how much.',
               months=['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December']),
    'ar': dict(dir='rtl', share='شارك', copy='انسخ الرابط', copied='تم النسخ', share_native='مشاركة…', which='أي محمد شرف؟', writing='كتابات', topics='المواضيع', all_topics='الكل', topic_intro='كل ما كتبته عن {topic}، الأحدث أولًا.', home='الرئيسية', menu='القائمة', hello='قل مرحبًا', other='English', other_lang='en',
               index_title='كتابات', index_intro='ملاحظات عن الأمن والبنية التحتية والبرمجيات والذكاء الاصطناعي، بكلام واضح، من ثلاثة عقود من العمل.',
               min_read='دقائق قراءة', back='كل الكتابات', cta_title='تحتاج إلى نظرة ثانية؟',
               cta_text='إذا بدا لك شيء هنا مثل نظامك، اكتب لي. أقرأ كل شيء.',
               cta_link='تواصل معي', draft='مسودة: لم تُنشر بعد', empty='أول المقالات في الطريق.',
               new_heading='جديد', archive_heading='من الأرشيف', archive_intro='ملاحظات من مدونتي القديمة على mohamedsharaf.net (2010–2018)، أُعيدت كتابتها ومراجعتها. بعضها قديم، والتاريخ يوضح كم.',
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
.share{max-width:720px;margin:0 auto 34px;padding-top:18px;border-top:1px solid var(--line);display:flex;flex-wrap:wrap;align-items:center;gap:8px 16px;font-size:14px}
.share>span{font:12px var(--mono);letter-spacing:.08em;text-transform:uppercase;color:var(--muted);margin-inline-end:4px}
[dir=rtl] .share>span{font-family:var(--sans);letter-spacing:0;font-size:13px}
.share a{color:var(--ink);text-underline-offset:4px;text-decoration-color:var(--orange)}
.share button{font:inherit;color:var(--ink);background:none;border:1px solid var(--line);padding:5px 10px;cursor:pointer}
.share button:hover,.share a:hover{color:var(--orange-ink)}
.cta{max-width:720px;margin:10px auto 70px;padding:28px;background:var(--ink);color:var(--paper);display:flex;justify-content:space-between;align-items:center;gap:24px;flex-wrap:wrap}
.cta h2{margin:0 0 6px;font-size:22px}
.cta p{margin:0;color:#c9c6bd;font-size:15px}
.cta a{background:#c9441f;color:#fff;padding:12px 18px;font-weight:600;text-decoration:none;white-space:nowrap}
.index{max-width:820px;margin:0 auto;padding:64px 0 80px}
.index h1{font-size:clamp(40px,7vw,64px);letter-spacing:-.05em;margin:14px 0 14px}
.kicker a{text-decoration:none}
.kicker a:hover{text-decoration:underline;text-underline-offset:3px}
.topics{display:flex;flex-wrap:wrap;gap:8px;margin:30px 0 0}
.topics a{display:inline-flex;align-items:baseline;gap:7px;padding:7px 11px;border:1px solid var(--line);background:var(--paper-card);font-size:14px;font-weight:600;text-decoration:none;white-space:nowrap}
.topics a span{font:12px var(--mono);color:var(--muted)}
.topics a:hover{border-color:var(--ink)}
.topics a[aria-current]{background:var(--ink);border-color:var(--ink);color:var(--paper)}
.topics a[aria-current] span{color:#c9c6bd}
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
@media(max-width:600px){.topics{flex-wrap:nowrap;overflow-x:auto;margin-inline:-20px;padding:0 20px 6px;scrollbar-width:thin}.nav .hide,.nav .hello{display:none}.nav{margin-inline-start:auto}.header{gap:10px}.menu{display:block}.article,.index{padding-top:40px}.body{font-size:16.5px}.cta{padding:22px}}
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
  <meta property="og:image:width" content="1200">
  <meta property="og:image:height" content="630">
  <meta name="twitter:card" content="summary_large_image">
  <link rel="icon" href="/favicon.svg" type="image/svg+xml">
  <link rel="apple-touch-icon" href="/apple-touch-icon.png">
  <link rel="alternate" type="application/atom+xml" title="{'Mohamed Sharaf — Writing' if lang == 'en' else 'محمد شرف — كتابات'}" href="{'/writing/feed.xml' if lang == 'en' else '/writing/ar/feed.xml'}">
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
    <a href="{'/which-mohamed-sharaf/' if lang == 'en' else '/which-mohamed-sharaf/ar/'}">{t['which']}</a>
    <a href="{'/writing/' if lang == 'en' else '/writing/ar/'}">{t['back']} {'→' if lang == 'en' else '←'}</a>
  </footer>
</body>
</html>
"""


def og_image_for(a):
    """The article's own share card from tools/make_og.py, or the site-wide card."""
    card = f"assets/og/{a['lang']}-{a['slug']}.jpg"
    if os.path.exists(os.path.join(ROOT, card)):
        return f'{SITE}/{card}'
    return f"{SITE}/assets/og-{'en' if a['lang'] == 'en' else 'ar'}.jpg"


def share_bar(a):
    """Plain share links (no third-party scripts); /assets/share.js adds copy link and the phone's share sheet."""
    t = TEXT[a['lang']]
    url = SITE + url_for(a)
    u, ti = quote(url, safe=''), quote(a['title'], safe='')
    links = [('WhatsApp', f'https://wa.me/?text={ti}%20{u}'),
             ('LinkedIn', f'https://www.linkedin.com/sharing/share-offsite/?url={u}'),
             ('X', f'https://x.com/intent/post?text={ti}&amp;url={u}'),
             ('Telegram', f'https://t.me/share/url?url={u}&amp;text={ti}'),
             ('Facebook', f'https://www.facebook.com/sharer/sharer.php?u={u}')]
    items = ''.join(f'<a href="{href}" target="_blank" rel="noopener noreferrer" lang="en">{name}</a>' for name, href in links)
    return (f'<div class="share" data-url="{html.escape(url)}" data-title="{html.escape(a["title"])}"><span>{t["share"]}</span>{items}'
            f'<button type="button" class="share-copy" data-done="{t["copied"]}" hidden>{t["copy"]}</button>'
            f'<button type="button" class="share-native" hidden>{t["share_native"]}</button></div>'
            '<script src="/assets/share.js?v=1" defer></script>')


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
        'image': og_image_for(a),
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
      {draft}<div class="kicker"><a href="{topic_url(a['lang'], a['topic'])}">{html.escape(a['topic'])}</a></div>
      <h1>{html.escape(a['title'])}</h1>
      <p class="lead">{html.escape(a['description'])}</p>
      <div class="meta"><time datetime="{a['date']}">{nice_date(a['date'], a['lang'])}</time> · {minutes} {t['min_read']}</div>
      {archive}<div class="body">
{a['body']}
      </div>
    </article>
    {share_bar(a)}
    <aside class="cta"><div><h2>{t['cta_title']}</h2><p>{t['cta_text']}</p></div><a href="{'/#contact' if a['lang'] == 'en' else '/ar#contact'}">{t['cta_link']}</a></aside>"""
    other = url_for(pair) if pair else other_index(a['lang'])
    return page(a['lang'], a['title'], a['description'], canonical, body, head, alternates, other, og_image_for(a))


def topic_slug(name):
    return re.sub(r'[^a-z0-9]+', '-', name.lower()).strip('-')


def topic_url(lang, topic):
    return f"{INDEX[lang]}topic/{TOPIC_SLUG[topic]}/"


def topic_nav(lang, items, current=None):
    # Plain links, one static page per topic: works without JavaScript and each topic page can be found in search
    t = TEXT[lang]
    counts = {}
    for a in items:
        counts[a['topic']] = counts.get(a['topic'], 0) + 1
    links = [(t['all_topics'], INDEX[lang], len(items), current is None)]
    links += [(name, topic_url(lang, name), n, name == current)
              for name, n in sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))]
    return f'      <nav class="topics" aria-label="{t["topics"]}">\n' + ''.join(
        f'        <a href="{u}"{" aria-current=\"page\"" if on else ""}>{html.escape(name)} <span>{n}</span></a>\n'
        for name, u, n, on in links) + '      </nav>\n'


def index_page(lang, all_items, topic=None):
    t = TEXT[lang]
    items = [a for a in all_items if a['topic'] == topic] if topic else all_items
    canonical = topic_url(lang, topic) if topic else INDEX[lang]
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
    if topic:
        kicker = f'<a href="{INDEX[lang]}">{t["writing"]}</a>'
        title, intro = topic, t['topic_intro'].format(topic=topic)
        # The same topic in the other language shares the English slug
        alternates = {l: f"{INDEX[l]}topic/{TOPIC_SLUG[topic]}/" for l in LANGS_WITH_ITEMS
                      if TOPIC_SLUG[topic] in TOPIC_SLUGS_BY_LANG.get(l, ())}
        other_url = next((u for l, u in alternates.items() if l != lang), other_index(lang))
    else:
        kicker = 'Mohamed Sharaf' if lang == 'en' else 'محمد شرف'
        title, intro = t['index_title'], t['index_intro']
        alternates = {l: INDEX[l] for l in LANGS_WITH_ITEMS}
        other_url = other_index(lang)
    body = f"""    <section class="index">
      <div class="kicker">{kicker}</div>
      <h1>{html.escape(title)}</h1>
      <p class="lead">{html.escape(intro)}</p>
{topic_nav(lang, all_items, topic)}{sections}    </section>"""
    return page(lang, f"{title} · {t['writing']}" if topic else title, intro, canonical, body,
                alternates=alternates, other_url=other_url)


def write(path, text):
    full = os.path.join(DIST, path.strip('/'), 'index.html')
    os.makedirs(os.path.dirname(full), exist_ok=True)
    open(full, 'w', encoding='utf-8').write(text)


INDEX = {'en': '/writing/', 'ar': '/writing/ar/'}
FEED_URLS = {'en': '/writing/feed.xml', 'ar': '/writing/ar/feed.xml'}


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
# Topic addresses use the English topic name, so an Arabic topic takes its slug from its English pair
TOPIC_SLUG = {a['topic']: topic_slug(a['topic']) for a in articles if a['lang'] == 'en'}
for a in articles:
    if a['topic'] not in TOPIC_SLUG:
        en = next((b for b in by_pair[a.get('pair') or a['slug']] if b['lang'] == 'en'), None)
        TOPIC_SLUG[a['topic']] = topic_slug(en['topic'] if en else a['topic']) or 'other'
TOPIC_SLUGS_BY_LANG = {}
for a in articles:
    TOPIC_SLUGS_BY_LANG.setdefault(a['lang'], set()).add(TOPIC_SLUG[a['topic']])
for a in articles:
    pair = next((b for b in by_pair[a.get('pair') or a['slug']] if b is not a), None)
    write(url_for(a), article_page(a, pair))
# Index pages only exist once a language has something to list
index_urls = []
topic_urls = []
for lang in ('en', 'ar'):
    items = sorted((a for a in articles if a['lang'] == lang), key=lambda a: a['date'], reverse=True)
    if items:
        url = '/writing/' if lang == 'en' else '/writing/ar/'
        write(url, index_page(lang, items))
        index_urls.append(url)
        for topic in sorted({a['topic'] for a in items}):
            write(topic_url(lang, topic), index_page(lang, items, topic))
            if any(a['status'] == 'published' and a['topic'] == topic for a in items):
                topic_urls.append(topic_url(lang, topic))

# "Which Mohamed Sharaf?": the name is shared with others, including the late Egyptian actor.
# A short page says who this site belongs to and where my real profiles are. It says nothing about him.
NAME_URLS = {'en': '/which-mohamed-sharaf/', 'ar': '/which-mohamed-sharaf/ar/'}
PROFILES = [('LinkedIn', 'https://www.linkedin.com/in/mohamed-ahmed-sharaf/'), ('GitHub', 'https://github.com/mohamedsharaf'),
            ('YouTube', 'https://www.youtube.com/@mohamedsharaf'), ('Facebook', 'https://www.facebook.com/Mohamed.Ahmed.Sharaf')]
NAME_PAGE = {
    'en': dict(title='Which Mohamed Sharaf?', kicker='About the name',
               description='This site belongs to Mohamed Sharaf, a security and technology consultant. Not the late Egyptian actor of the same name.',
               body="""<p>Mohamed Sharaf is a common name, so here is which one this site belongs to.</p>
<p>I am a security and technology consultant based in Riyadh. I have been with computers since 1996, in information security since 2000, and running my own company since 2002. I write here about security, infrastructure, software and AI.</p>
<h2>Not the actor</h2>
<p>If you are looking for the late Egyptian actor Mohamed Sharaf, may he rest in peace, this is not him. We only share a name. Nothing on this site is about him or his work.</p>
<h2>Where to find me</h2>
<p>These are my only profiles. Anything else under this name that isn’t linked from this site is not me.</p>
<ul>
{profiles}
</ul>""", home='Back to the homepage', contact='Say hello'),
    'ar': dict(title='أي محمد شرف؟', kicker='عن الاسم',
               description='هذا موقع محمد شرف، مستشار أمن المعلومات والتقنية، وليس الفنان المصري الراحل الذي يحمل الاسم نفسه.',
               body="""<p>اسم محمد شرف منتشر، لذلك أوضح هنا لمن يعود هذا الموقع.</p>
<p>أنا مستشار في أمن المعلومات والتقنية، مقيم في الرياض. مع الكمبيوتر منذ 1996، وفي أمن المعلومات منذ 2000، وأدير شركتي الخاصة منذ 2002. أكتب هنا عن الأمن والبنية التحتية والبرمجيات والذكاء الاصطناعي.</p>
<h2>لست الفنان</h2>
<p>إذا كنت تبحث عن الفنان المصري الراحل محمد شرف، رحمه الله، فهذا ليس موقعه. نحن نشترك في الاسم فقط، ولا شيء في هذا الموقع عنه أو عن أعماله.</p>
<h2>أين تجدني</h2>
<p>هذه حساباتي الوحيدة، وأي حساب آخر بهذا الاسم لا يوجد له رابط من هذا الموقع فهو ليس لي.</p>
<ul>
{profiles}
</ul>""", home='العودة إلى الرئيسية', contact='تواصل معي'),
}
for lang, n in NAME_PAGE.items():
    profiles = '\n'.join(f'  <li><a href="{u}" lang="en">{name}</a></li>' for name, u in PROFILES)
    ld = {'@context': 'https://schema.org', '@type': 'AboutPage', 'name': n['title'], 'description': n['description'],
          'url': SITE + NAME_URLS[lang], 'inLanguage': lang, 'isPartOf': {'@id': f'{SITE}/#site'},
          'about': {'@id': f'{SITE}/#person'}, 'mainEntity': {'@id': f'{SITE}/#person'}}
    home = '/' if lang == 'en' else '/ar'
    body = f"""    <article class="article">
      <div class="kicker">{n['kicker']}</div>
      <h1>{n['title']}</h1>
      <p class="lead">{html.escape(n['description'])}</p>
      <div class="body">
{n['body'].format(profiles=profiles)}
<p><a href="{home}">{n['home']}</a> · <a href="{home}#contact">{n['contact']}</a></p>
      </div>
    </article>"""
    other = 'ar' if lang == 'en' else 'en'
    write(NAME_URLS[lang], page(lang, n['title'], n['description'], NAME_URLS[lang], body,
                                f'<script type="application/ld+json">{json.dumps(ld, ensure_ascii=False)}</script>\n  ',
                                alternates=NAME_URLS, other_url=NAME_URLS[other]).replace('<meta property="og:type" content="article">', '<meta property="og:type" content="profile">'))

# Add the writing pages and published articles to the sitemap (never drafts)
published = [a for a in articles if a.get('status') == 'published']
public_urls = [u for u in index_urls if any(a['lang'] == ('en' if u == '/writing/' else 'ar') for a in published)]
extra = ''.join(f"  <url>\n    <loc>{SITE}{u}</loc>\n  </url>\n" for u in public_urls + topic_urls + [url_for(a) for a in published] + list(NAME_URLS.values()))
if extra:
    sitemap = os.path.join(DIST, 'sitemap.xml')
    s = open(sitemap, encoding='utf-8').read().replace('</urlset>', extra + '</urlset>')
    open(sitemap, 'w', encoding='utf-8').write(s)

# Atom feeds, one per language, with the full text of the newest articles
FEED_TITLE = {'en': 'Mohamed Sharaf — Writing', 'ar': 'محمد شرف — كتابات'}
for lang in sorted({a['lang'] for a in published}):
    items = sorted((a for a in published if a['lang'] == lang), key=lambda a: a['date'], reverse=True)[:30]
    stamp = lambda d: f'{d}T00:00:00Z'
    entries = ''.join(f"""  <entry>
    <title>{html.escape(a['title'])}</title>
    <link href="{SITE}{url_for(a)}"/>
    <id>{SITE}{url_for(a)}</id>
    <published>{stamp(a['date'])}</published>
    <updated>{stamp(a.get('updated', a['date']))}</updated>
    <summary>{html.escape(a['description'])}</summary>
    <content type="html">{html.escape(a['body'])}</content>
  </entry>
""" for a in items)
    feed = f"""<?xml version="1.0" encoding="utf-8"?>
<feed xmlns="http://www.w3.org/2005/Atom" xml:lang="{lang}" xml:base="{SITE}/">
  <title>{FEED_TITLE[lang]}</title>
  <subtitle>{html.escape(TEXT[lang]['index_intro'])}</subtitle>
  <link href="{SITE}{FEED_URLS[lang]}" rel="self"/>
  <link href="{SITE}{INDEX[lang]}"/>
  <id>{SITE}{FEED_URLS[lang]}</id>
  <updated>{stamp(max(a.get('updated', a['date']) for a in items))}</updated>
  <author><name>{'Mohamed Sharaf' if lang == 'en' else 'محمد شرف'}</name><uri>{SITE}/</uri></author>
{entries}</feed>
"""
    open(os.path.join(DIST, FEED_URLS[lang].strip('/')), 'w', encoding='utf-8').write(feed)

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


def normal(src):
    """Cloudflare compares paths with the percent-encoding in capitals: /%d8%a7/ and /%D8%A7/ are one rule."""
    src = quote(src, safe="/%:*!$&'()+,;=-._~@")
    return re.sub(r'%[0-9a-fA-F]{2}', lambda m: m.group(0).upper(), src)


def variants(src):
    """Other spellings of an old address that WordPress also answered: with and without the
    trailing slash, and a post's feed, AMP and comment pages."""
    if '*' in src or ':' in src or src == '/':
        return []
    base = normal(src).rstrip('/') + '/'
    out = [base, base[:-1]]
    if base.count('/') == 2:  # a top-level post or page
        out += [base + 'feed/', base + 'feed', base + 'amp/', base + 'amp', base + 'comment-page-1/', base + 'comment-page-2/']
    return out


exact = [(s, d) for s, d in rules if '*' not in s]
rules = exact + [(v, d) for s, d in exact for v in variants(s)] + [(s, d) for s, d in rules if '*' in s]
lines = []
for src, dst in rules:
    src = src if '*' in src else normal(src)
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
    if show:
        feed_link = f'<link rel="alternate" type="application/atom+xml" title="{"Mohamed Sharaf — Writing" if lang == "en" else "محمد شرف — كتابات"}" href="{FEED_URLS[lang]}">\n</head>'
        page_html = page_html.replace('</head>', feed_link, 1)
    open(path, 'w', encoding='utf-8').write(page_html)
print(f"writing: {len(articles)} article(s) built ({len(published)} published), {len(lines)} redirect rules{' [PREVIEW: drafts included]' if PREVIEW else ''}")
