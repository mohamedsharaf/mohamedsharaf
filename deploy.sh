#!/bin/sh
# Builds the site and deploys it to Cloudflare Workers (see wrangler.toml).
# Needs a one-time `npx wrangler login`.
set -eu
cd "$(dirname "$0")"

sh build.sh
npx -y wrangler@4 deploy
