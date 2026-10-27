"""Helper for writing restored posts from the old mohamedsharaf.net blog into writing/.

Each restored post becomes writing/<slug>.en.html and writing/<slug>.ar.html with the
JSON header that tools/build_writing.py reads, plus a consistent "From the archive" note.

kind="own":     the author's own note, rewritten and checked
kind="summary": someone else's article that was shared on the old blog; we publish a
                short summary in our own words and credit the original
"""
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MONTHS_EN = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December']
MONTHS_AR = ['يناير', 'فبراير', 'مارس', 'أبريل', 'مايو', 'يونيو', 'يوليو', 'أغسطس', 'سبتمبر', 'أكتوبر', 'نوفمبر', 'ديسمبر']


def _note(kind, date, lang, source):
    y, m = int(date[:4]), int(date[5:7])
    if kind == 'summary':
        if lang == 'en':
            return (f"From the archive: in {y} I shared “{source['title']}” by {source['author']} on my old blog. "
                    "This page is a short summary in my own words; the original belongs to its author.")
        return (f"من الأرشيف: شاركتُ عام {y} مقال «{source['title']}» لـ{source['author_ar']} على مدونتي القديمة. "
                "هذه الصفحة ملخص قصير بكلماتي، والمقال الأصلي ملك لكاتبه.")
    if lang == 'en':
        return (f"From the archive: first published on mohamedsharaf.net in {MONTHS_EN[m - 1]} {y}. "
                "Rewritten and checked in 2026; some details may be out of date.")
    return (f"من الأرشيف: نُشر أصلًا على mohamedsharaf.net في {MONTHS_AR[m - 1]} {y}. "
            "أُعيدت كتابته ومراجعته في 2026، وبعض التفاصيل قد تكون قديمة.")


def _source_box(source, lang):
    if not source:
        return ''
    if lang == 'en':
        return f'\n<p class="note">Read the original: <a href="{source["url"]}">{source["title"]}</a>, by {source["author"]}.</p>'
    return f'\n<p class="note">اقرأ المقال الأصلي: <a href="{source["url"]}" lang="en">{source["title"]}</a>، بقلم {source["author_ar"]}.</p>'


def article(slug, date, kind, topic, en, ar, source=None, custom_note=None):
    """en/ar: dicts with title, description, body (HTML). topic: (english, arabic).
    custom_note: optional (english, arabic) archive note, e.g. when the original author is unknown."""
    for lang, data, topic_label in (('en', en, topic[0]), ('ar', ar, topic[1])):
        meta = {
            'slug': slug, 'lang': lang, 'pair': slug, 'status': 'published', 'archive': True,
            'title': data['title'], 'description': data['description'],
            'date': date, 'updated': '2026-10-27', 'topic': topic_label,
            'archive_note': (custom_note[0] if lang == 'en' else custom_note[1]) if custom_note else _note(kind, date, lang, source),
        }
        body = data['body'].strip() + _source_box(source, lang)
        path = os.path.join(ROOT, 'writing', f'{slug}.{lang}.html')
        with open(path, 'w', encoding='utf-8') as f:
            f.write('<!--\n' + json.dumps(meta, ensure_ascii=False, indent=1) + '\n-->\n' + body + '\n')
    return slug
