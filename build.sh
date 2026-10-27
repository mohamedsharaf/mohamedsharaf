#!/bin/sh
# Builds the public website into dist/ for Cloudflare Workers.
#
# Only the files listed below are published. docs/ (old versions, portrait
# options, source photos) and anything else in this folder stay private.
# Add a new page here if you create one.
#
# Deploy (build + upload to Cloudflare Workers): sh deploy.sh
set -eu
cd "$(dirname "$0")"

rm -rf dist
mkdir dist
cp index.html ar.html 404.html robots.txt sitemap.xml llms.txt favicon.svg apple-touch-icon.png dist/
cp -R assets dist/assets
cp -R .well-known dist/.well-known
find dist -name '.DS_Store' -delete

# Security and cache headers (Cloudflare reads dist/_headers).
# The Content-Security-Policy only allows the pages' own inline scripts, by hash,
# so the hashes are recalculated here on every build.
python3 - <<'PY'
import base64, hashlib, re
hashes = []
for page in ('dist/index.html', 'dist/ar.html', 'dist/404.html'):
    html = open(page, encoding='utf-8').read()
    for script in re.findall(r'<script>(.*?)</script>', html, re.S):
        digest = base64.b64encode(hashlib.sha256(script.encode('utf-8')).digest()).decode()
        hashes.append(f"'sha256-{digest}'")
csp = '; '.join([
    "default-src 'self'",
    "script-src 'self' " + ' '.join(sorted(set(hashes))),
    "style-src 'self' 'unsafe-inline'",
    "img-src 'self' data:",
    "font-src 'self'",
    "connect-src 'self' https://formsubmit.co",
    "form-action 'self' https://formsubmit.co",
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
""")
PY

# Safety net: refuse to build if anything private slipped in
if [ -e dist/docs ] || find dist -name '*.md' | grep -q .; then
  echo "build.sh: private files found in dist/, stopping." >&2
  exit 1
fi

echo "Built dist/ with $(find dist -type f | wc -l | tr -d ' ') files:"
find dist -type f | sort
