# Writing guide

How articles for mohamedsharaf.com/writing are written, added and built, and the rules they follow. Read it before writing any new article.

## Where articles live

Each article is one file per language in `writing/`:

```text
writing/<slug>.en.html   → https://mohamedsharaf.com/writing/<slug>/
writing/<slug>.ar.html   → https://mohamedsharaf.com/writing/ar/<slug>/
```

A file is an HTML fragment that starts with a JSON header inside an HTML comment:

```html
<!--
{"slug": "renewals-calendar", "lang": "en", "pair": "renewals-calendar", "status": "published",
 "title": "Put every renewal date in one calendar",
 "description": "Domains, certificates, licences, support contracts and payment cards all expire.",
 "date": "2026-10-26", "topic": "Infrastructure"}
-->
<p>Article body…</p>
```

### Header fields

| Field | Required | Notes |
|---|---|---|
| `slug` | yes | Lowercase words joined by hyphens, short and unique. Check `ls writing/` first. Same slug in both languages. |
| `lang` | yes | `en` or `ar` |
| `pair` | yes | The slug of the other language’s version (normally the same slug). Links the two as translations. |
| `status` | yes | `published`, or `draft`. Drafts are only built with `PREVIEW=1 sh build.sh` and never reach the live site. |
| `title` | yes | At most 50 characters (see the checks below). |
| `description` | yes | One or two sentences, about 120–160 characters. Used for search results, social cards and the writing list. |
| `date` | yes | `YYYY-MM-DD`, a weekday. Sorting, feeds and the homepage use it. |
| `topic` | yes | One of the topics below, in the article’s language. |
| `updated` | no | `YYYY-MM-DD` when an article is meaningfully revised. |
| `archive`, `archive_note` | no | Only for posts rewritten from the old blog (2010–2018). Not used for new articles. |

### Topics

Use one of these. The English name decides the topic page address (`/writing/topic/<name>/`), and the Arabic version takes it from its English pair.

| English | Arabic |
|---|---|
| Security | أمن المعلومات |
| Infrastructure | البنية التحتية |
| Software | البرمجيات |
| Privacy | الخصوصية |
| AI | الذكاء الاصطناعي |

Older archive topics (Servers, WordPress, Zend Framework, Databases, Web, PHP, Windows) exist for old posts. Don’t create new topics without asking the owner. Small topics clutter the filter row.

### Body HTML

Plain, semantic HTML only: `<p>`, `<ul>`/`<ol>`/`<li>`, `<strong>`, `<em>`, `<code>`, `<pre><code>`, `<a>`, `<blockquote>`, `<h2>`/`<h3>`, and `<p class="note">` for a boxed note. No inline styles, scripts, images or iframes. The page adds the title, description, date, reading time, share bar and contact box, so the body starts straight with the first paragraph.

Links to other articles use `/writing/<slug>/` (English) or `/writing/ar/<slug>/` (Arabic). A link to an article that isn’t published becomes plain text automatically.

## Adding articles

1. **Write a batch file outside the repo** (for example in a scratch folder). It’s a Python file with one list:

   ```python
   ARTICLES = [
   ("renewals-calendar", "en", "2026-10-26", "Infrastructure", "Put every renewal date in one calendar",
    "Domains, certificates, licences, support contracts and payment cards all expire. ...",
   """
   <p>...</p>
   """),
   ("renewals-calendar", "ar", "2026-10-26", "البنية التحتية", "ضع كل مواعيد التجديد في تقويم واحد",
    "...",
   """
   <p>...</p>
   """),
   ]
   ```

   English first, then Arabic, same slug and date. Group a month or a few articles per file.

2. **Write the files:** `python3 tools/add_articles.py path/to/batch.py`. It creates `writing/<slug>.<lang>.html` with the header filled in and `status: published`. Running it again overwrites the same files.

3. **Check every article has its pair:**

   ```bash
   git status --porcelain writing | sed -E 's#^\?\? writing/##; s#\.(en|ar)\.html$##' | sort | uniq -c | awk '$1!=2'
   ```

   No output means every new slug has both languages.

4. **Make the share cards:** `python3 tools/make_og.py`. It draws `assets/og/<lang>-<slug>.jpg` for new or changed articles only (needs Google Chrome and macOS `sips`).

5. **Build:** `bash build.sh`. This also refreshes the writing lists, topic pages, the homepage’s latest notes, feeds and the sitemap.

6. **Validate the new pages:**

   ```bash
   npx -y html-validate -f text dist/writing/<slug>/index.html dist/writing/ar/<slug>/index.html | grep -v doctype-style
   ```

   The site uses a lowercase doctype on purpose, so ignore `doctype-style`. Fix anything else. The usual one is `long-title`: the page title is the article title plus “ — Mohamed Sharaf”, and must stay under 70 characters, so keep titles at 50 or less.

7. **Preview** with the `site` launch configuration (`wrangler dev` on port 8795) or Valet at `mohamedsharaf.test`.

8. **Commit locally.** One commit per batch, for example “Add 8 short articles for November 2026”.

9. **Deploy only when the owner clearly asks** (“deploy”, “انشر”, “ارفع”). Then `sh deploy.sh`, check the live pages, and push to GitHub when asked. Approving a change or a commit is not a deploy request. The Cloudflare account is on the free plan.

## Style

The owner wants short articles that sound like a person wrote them, not an AI.

- **Short.** About 120–250 words. Get to the point in the first sentence. No long introduction, no summary at the end.
- **One shape:** a short opening (what happened, or what the problem is), why it matters in one or two sentences, then one list of concrete actions. Sometimes a closing line, if it adds something.
- **Concrete.** Name the setting, the menu, the command or the version number. “Turn on Protect Mail Activity in Mail settings” beats “review your privacy settings”.
- **Plain words.** Write for a busy manager and a working sysadmin at the same time.
- **First person when natural:** “I’ve seen”, “in almost every audit I find”. Not in every article.
- **Uneven rhythm.** Vary sentence length. A two-word sentence is fine.
- **Avoid AI tells:** “In today’s world”, “Here’s the thing”, “Let’s dive in”, “It’s not just X, it’s Y”, a bolded lead-in on every bullet, lists of exactly three everywhere, closing aphorisms on every article, em-dash chains, perfectly symmetrical sections. Bold lead-ins are fine sometimes, not always.
- **Spelling:** British English (organisation, licence, defence).

### Arabic

- Modern Standard Arabic that reads naturally. Translate the meaning, not word by word.
- Keep product names, commands, CVE numbers and versions in Latin script: Microsoft 365، CVE-2026-20700، PHP 8.3.
- Use Western digits (2026, 15 مارس) and Arabic punctuation (، ؛ ؟).
- Topic names from the table above, exactly.
- Same facts, dates and numbers as the English version, and roughly the same length.

## Accuracy and ethics

- **Real events only.** For news-based articles, check the facts with web search, and use only what more than one reliable source reports. Unconfirmed figures, especially numbers claimed by attackers, are written as “reports say” or left out.
- **Dates match the facts.** An article is dated on or after the event it describes. Words like “yesterday”, “this week” and “last month” are relative to the article’s date. Never mention something that happened after the article’s date.
- **Nothing invented.** No made-up anecdotes, clients, quotes, testimonials or numbers.
- **No client names, ever**, and no company or employer names for the owner’s own work. This matches the homepage promise.
- **People:** use gender-neutral wording for real people whose pronouns you don’t know (“the researcher”, “they”). In Arabic, phrase around the person (“the account of…”) instead of guessing the gender.
- **Don’t copy.** Summarise other people’s work in your own words and link the source when the article is based on it.
- **Practical over scary.** Every article ends with something the reader can do.

## Cadence

About two articles a month going forward, on weekdays, in both languages. Mix one news-based piece with one practical piece when possible. Pick from the owner’s fields: security, infrastructure, software, privacy and AI.
