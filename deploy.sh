#!/bin/sh
# Builds the site and deploys it to Cloudflare Pages (project "mohamedsharaf").
# Needs a one-time `npx wrangler login`. The first run also creates the project.
set -eu
cd "$(dirname "$0")"

sh build.sh

if ! npx -y wrangler@4 pages project list 2>/dev/null | grep -q "│ mohamedsharaf "; then
  npx -y wrangler@4 pages project create mohamedsharaf --production-branch main
fi

npx -y wrangler@4 pages deploy dist --project-name mohamedsharaf --branch main --commit-dirty=true
