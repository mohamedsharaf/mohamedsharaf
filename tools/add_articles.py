#!/usr/bin/env python3
"""Writes a batch of articles into writing/ from a Python file that defines
ARTICLES = [(slug, lang, date, topic, title, description, body_html), ...]

Usage: python3 tools/add_articles.py path/to/batch.py
Then: python3 tools/make_og.py && bash build.sh
"""
import importlib.util
import json
import os
import sys

ROOT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'writing')
spec = importlib.util.spec_from_file_location('batch', sys.argv[1])
batch = importlib.util.module_from_spec(spec)
spec.loader.exec_module(batch)
for slug, lang, date, topic, title, description, body in batch.ARTICLES:
    meta = {'slug': slug, 'lang': lang, 'pair': slug, 'status': 'published', 'title': title,
            'description': description, 'date': date, 'topic': topic}
    with open(os.path.join(ROOT, f'{slug}.{lang}.html'), 'w', encoding='utf-8') as f:
        f.write('<!--\n' + json.dumps(meta, ensure_ascii=False) + '\n-->\n' + body.strip() + '\n')
print(f'wrote {len(batch.ARTICLES)} article file(s) into writing/')
