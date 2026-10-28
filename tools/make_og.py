#!/usr/bin/env python3
"""Makes a share image (1200x630 JPEG) for every published article in writing/.

The card is an HTML page in the site's style, photographed with headless Chrome,
then converted to JPEG with macOS `sips`. Cards are saved as assets/og/<lang>-<slug>.jpg
and only redrawn when the article's title, topic or date changes (assets/og/manifest.json).
tools/build_writing.py uses a card when it exists, and the site-wide card otherwise.

Usage: python3 tools/make_og.py            (new or changed cards only)
       python3 tools/make_og.py --all      (redraw every card)
"""
import hashlib
import html
import json
import os
import re
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, 'assets', 'og')
CHROME = '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'
VERSION = '1'  # bump to redraw every card after a template change

TEMPLATE = """<!doctype html>
<html lang="{lang}" dir="{dir}">
<head>
<meta charset="utf-8">
<style>
  @font-face{{font-family:Manrope;src:url('{assets}/manrope-latin.woff2') format('woff2');font-weight:200 800}}
  @font-face{{font-family:'IBM Plex Sans Arabic';src:url('{assets}/plex-arabic-400.woff2') format('woff2');font-weight:400}}
  @font-face{{font-family:'IBM Plex Sans Arabic';src:url('{assets}/plex-arabic-600.woff2') format('woff2');font-weight:600}}
  *{{box-sizing:border-box;margin:0}}
  html,body{{width:1200px;height:630px;overflow:hidden}}
  body{{background:#eeeae2;color:#242624;font-family:Manrope,'IBM Plex Sans Arabic',sans-serif;display:grid;grid-template-columns:1fr 330px}}
  .copy{{padding:58px 68px 50px;display:flex;flex-direction:column;min-width:0}}
  .brand{{display:flex;align-items:center;gap:14px;font-size:25px;font-weight:750;letter-spacing:-.8px}}
  [dir=rtl] .brand{{letter-spacing:0;font-weight:600}}
  .sym{{display:grid;grid-template-columns:repeat(2,10px);gap:4px;transform:rotate(-7deg)}}
  .sym i{{width:10px;height:10px;background:#e85532}}
  .sym i:last-child{{opacity:.35}}
  .kicker{{margin-top:44px;font:600 18px 'SFMono-Regular',Menlo,monospace;letter-spacing:.07em;text-transform:uppercase;color:#ad3a1c}}
  [dir=rtl] .kicker{{font:600 22px 'IBM Plex Sans Arabic',sans-serif;letter-spacing:0}}
  .title-box{{flex:1;min-height:0;margin-top:18px;overflow:hidden}}
  h1{{font-size:72px;line-height:1.08;letter-spacing:-.045em;font-weight:700}}
  [dir=rtl] h1{{line-height:1.4;letter-spacing:0;font-weight:600}}
  .foot{{display:flex;justify-content:space-between;gap:20px;font:17px 'SFMono-Regular',Menlo,monospace;color:#5f6059;letter-spacing:.03em;border-top:1px solid #cecdc4;padding-top:16px}}
  [dir=rtl] .foot{{font:20px 'IBM Plex Sans Arabic',sans-serif;letter-spacing:0}}
  .foot b{{font-weight:400;direction:ltr;unicode-bidi:isolate}}
  .photo{{background:#1d2128 url('{assets}/mohamedsharaf.jpg') center 22%/cover no-repeat;position:relative}}
  .photo::after{{content:'';position:absolute;inset:0;border-inline-start:6px solid #e85532}}
</style>
</head>
<body>
  <div class="copy">
    <div class="brand"><span class="sym"><i></i><i></i><i></i><i></i></span>{name}</div>
    <div class="kicker">{kicker}</div>
    <div class="title-box"><h1 id="t">{title}</h1></div>
    <div class="foot"><b>{url}</b><span>{label}</span></div>
  </div>
  <div class="photo"></div>
<script>
  // Shrink long titles until they fit their box
  const t = document.getElementById('t'), box = t.parentElement;
  let size = 72;
  document.fonts.ready.then(() => {{
    while (t.scrollHeight > box.clientHeight && size > 34) {{ size -= 2; t.style.fontSize = size + 'px'; }}
    document.title = 'ready';
  }});
</script>
</body>
</html>
"""


def articles():
    folder = os.path.join(ROOT, 'writing')
    for name in sorted(os.listdir(folder)):
        if not name.endswith('.html'):
            continue
        raw = open(os.path.join(folder, name), encoding='utf-8').read()
        meta = json.loads(re.match(r'\s*<!--\s*(\{.*?\})\s*-->', raw, re.S).group(1))
        if meta.get('status') == 'published':
            yield meta


def card_html(a):
    ar = a['lang'] == 'ar'
    year = a['date'][:4]
    topic = a.get('topic', '')
    if a.get('archive'):
        kicker = f"{topic} · من الأرشيف · {year}" if ar else f"{topic} · From the archive · {year}"
    else:
        kicker = topic
    url = f"mohamedsharaf.com/writing/{'ar/' if ar else ''}{a['slug']}/"
    return TEMPLATE.format(
        lang=a['lang'], dir='rtl' if ar else 'ltr', assets='file://' + os.path.join(ROOT, 'assets'),
        name='محمد شرف' if ar else 'Mohamed Sharaf', kicker=html.escape(kicker), title=html.escape(a['title']),
        url=html.escape(url) if len(url) <= 58 else 'mohamedsharaf.com/writing', label='كتابات' if ar else 'Writing')


def main():
    redraw_all = '--all' in sys.argv
    os.makedirs(OUT, exist_ok=True)
    manifest_path = os.path.join(OUT, 'manifest.json')
    manifest = json.load(open(manifest_path)) if os.path.exists(manifest_path) and not redraw_all else {}
    made = kept = 0
    with tempfile.TemporaryDirectory() as tmp:
        profile = os.path.join(tmp, 'profile')
        for a in articles():
            key = f"{a['lang']}-{a['slug']}"
            page = card_html(a)
            digest = hashlib.sha256((VERSION + page).encode('utf-8')).hexdigest()[:16]
            jpg = os.path.join(OUT, key + '.jpg')
            if manifest.get(key) == digest and os.path.exists(jpg):
                kept += 1
                continue
            src, png = os.path.join(tmp, key + '.html'), os.path.join(tmp, key + '.png')
            open(src, 'w', encoding='utf-8').write(page)
            subprocess.run([CHROME, '--headless=new', '--disable-gpu', '--hide-scrollbars', '--force-device-scale-factor=1',
                            '--window-size=1200,630', '--virtual-time-budget=4000', f'--user-data-dir={profile}',
                            '--allow-file-access-from-files', f'--screenshot={png}', 'file://' + src],
                           check=True, capture_output=True)
            subprocess.run(['sips', '-s', 'format', 'jpeg', '-s', 'formatOptions', '82', png, '--out', jpg],
                           check=True, capture_output=True)
            manifest[key] = digest
            made += 1
    json.dump(dict(sorted(manifest.items())), open(manifest_path, 'w'), indent=1)
    print(f'og: {made} card(s) drawn, {kept} unchanged, in assets/og/')


if __name__ == '__main__':
    main()
