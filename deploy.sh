#!/bin/sh
# Builds the site and deploys it to Cloudflare Workers (see wrangler.toml).
# Needs a one-time `npx wrangler login`.
set -eu
cd "$(dirname "$0")"

# The contact form's Turnstile sitekey (public, from the Turnstile widget in the dashboard)
TURNSTILE_SITEKEY="${TURNSTILE_SITEKEY:-0x4AAAAAAADDmp5mB86tmuP2}"
case "$TURNSTILE_SITEKEY" in
  ''|1x*|2x*|3x*) echo "deploy: set TURNSTILE_SITEKEY in deploy.sh to the real Turnstile sitekey first" >&2; exit 1 ;;
esac
export TURNSTILE_SITEKEY

# Cloudflare Web Analytics site token (public, from Web Analytics in the dashboard)
CF_BEACON_TOKEN="${CF_BEACON_TOKEN:-acdfb99965524624b43cba8907135d9b}"
export CF_BEACON_TOKEN

sh build.sh
npx -y wrangler@4 deploy
