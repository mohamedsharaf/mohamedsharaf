# mohamedsharaf.com

Personal and consulting site of Mohamed Sharaf, in English (`index.html`) and Arabic (`ar.html`), served as a Cloudflare Worker with static assets.

- **Writing articles:** follow [docs/writing-guide.md](docs/writing-guide.md) for the format, the steps (`tools/add_articles.py`, `tools/make_og.py`, `build.sh`) and the style and accuracy rules.
- **Plan:** what’s left to do is in [docs/plan.md](docs/plan.md).
- **Build:** `bash build.sh` writes the public site to `dist/`. Only the files listed in `build.sh` are published, so `docs/` stays private.
- **Preview:** the `site` launch configuration (`wrangler dev` on port 8795), or Valet at `mohamedsharaf.test`.
- **Deploy:** only when the owner clearly asks in the conversation. Then `sh deploy.sh`. The account is on the Cloudflare free plan. Commit locally, and push to GitHub only when asked.
- **Public repo:** this repository is public. Never commit secrets, the WordPress SQL backup, client names or anything from `docs/private/`.
