#!/bin/sh
# Builds the public website into dist/ for Cloudflare Workers.
#
# Only the files listed below are published. docs/ (old versions, portrait
# options, source photos) and anything else in this folder stay private.
# Add a new page here if you create one.
#
# Deploy (build + upload to Cloudflare Workers): sh deploy.sh
# Preview drafts locally:                         PREVIEW=1 sh build.sh
set -eu
cd "$(dirname "$0")"

rm -rf dist
mkdir dist
cp index.html ar.html 404.html robots.txt sitemap.xml llms.txt favicon.svg apple-touch-icon.png dist/
cp -R assets dist/assets
rm -f dist/assets/og/manifest.json  # bookkeeping for tools/make_og.py, not a public file
cp -R .well-known dist/.well-known
find dist -name '.DS_Store' -delete

# Turnstile sitekey for the contact form (public). Without TURNSTILE_SITEKEY the build uses
# Cloudflare's test key, which only works locally; deploy.sh refuses to publish it.
TURNSTILE_SITEKEY="${TURNSTILE_SITEKEY:-1x00000000000000000000AA}"
python3 - "$TURNSTILE_SITEKEY" <<'PY'
import re, sys
key = sys.argv[1]
assert re.fullmatch(r'[0-9A-Za-z_-]{10,64}', key), 'bad TURNSTILE_SITEKEY'
for page in ('dist/index.html', 'dist/ar.html'):
    html = open(page, encoding='utf-8').read()
    assert '__TURNSTILE_SITEKEY__' in html, page
    open(page, 'w', encoding='utf-8').write(html.replace('__TURNSTILE_SITEKEY__', key))
PY

# Articles in writing/ become /writing/... pages (drafts only with PREVIEW=1)
python3 tools/build_writing.py dist

# Cloudflare Web Analytics (no cookies). Only when CF_BEACON_TOKEN is set, so local
# builds never report visits; deploy.sh sets it.
CF_BEACON_TOKEN="${CF_BEACON_TOKEN:-}"
python3 - "$CF_BEACON_TOKEN" <<'PY'
import os, re, sys
token = sys.argv[1]
if token:
    assert re.fullmatch(r'[0-9a-f]{32}', token), 'bad CF_BEACON_TOKEN'
    tag = ("<script defer src=\"https://static.cloudflareinsights.com/beacon.min.js\" "
           f"data-cf-beacon='{{\"token\": \"{token}\"}}'></script>\n</body>")
    for folder, _, files in os.walk('dist'):
        for name in files:
            if name.endswith('.html'):
                path = os.path.join(folder, name)
                html = open(path, encoding='utf-8').read()
                assert html.count('</body>') == 1, path
                open(path, 'w', encoding='utf-8').write(html.replace('</body>', tag))
PY

# Security and cache headers (Cloudflare reads dist/_headers).
# The Content-Security-Policy only allows the pages' own inline scripts, by hash,
# so the hashes are recalculated here on every build.
python3 - "$CF_BEACON_TOKEN" <<'PY'
import base64, hashlib, re, sys
beacon = bool(sys.argv[1])
hashes = []
for page in ('dist/index.html', 'dist/ar.html', 'dist/404.html'):
    html = open(page, encoding='utf-8').read()
    for script in re.findall(r'<script>(.*?)</script>', html, re.S):
        digest = base64.b64encode(hashlib.sha256(script.encode('utf-8')).digest()).decode()
        hashes.append(f"'sha256-{digest}'")
csp = '; '.join([
    "default-src 'self'",
    "script-src 'self' https://challenges.cloudflare.com " + ('https://static.cloudflareinsights.com ' if beacon else '') + ' '.join(sorted(set(hashes))),
    "frame-src https://challenges.cloudflare.com",
    "style-src 'self' 'unsafe-inline'",
    "img-src 'self' data:",
    "font-src 'self'",
    "connect-src 'self'" + (' https://cloudflareinsights.com' if beacon else ''),
    "form-action 'self'",
    "frame-ancestors 'none'",
    "base-uri 'self'",
    "object-src 'none'",
])
open('dist/_headers', 'w').write(f"""/*
  Content-Security-Policy: {csp}
  X-Content-Type-Options: nosniff
  X-Frame-Options: DENY
  Referrer-Policy: strict-origin-when-cross-origin
  Permissions-Policy: camera=(), microphone=(), geolocation=(), payment=(), usb=()
  Cross-Origin-Opener-Policy: same-origin
  Strict-Transport-Security: max-age=31536000

/assets/*
  Cache-Control: public, max-age=604800, stale-while-revalidate=86400

/writing/feed.xml
  Content-Type: application/atom+xml; charset=utf-8

/writing/ar/feed.xml
  Content-Type: application/atom+xml; charset=utf-8
""")
PY

# Safety net: refuse to build if anything private slipped in
if [ -e dist/docs ] || find dist -name '*.md' | grep -q .; then
  echo "build.sh: private files found in dist/, stopping." >&2
  exit 1
fi

echo "Built dist/ with $(find dist -type f | wc -l | tr -d ' ') files:"
find dist -type f | sort
