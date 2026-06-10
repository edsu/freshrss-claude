#!/usr/bin/env python3
"""Load and strip articles from a saved MCP result file.

Usage: load_articles.py <json_path>

Outputs articles as JSON to stdout with HTML stripped from summaries.
Article count goes to stderr.
"""
import html
import json
import re
import sys


def strip_html(s):
    s = re.sub(r"<[^>]+>", "", s or "")
    s = html.unescape(s)
    return re.sub(r"\s+", " ", s).strip()


json_path = sys.argv[1]

with open(json_path) as f:
    data = json.load(f)
articles = data["result"]

for a in articles:
    a["summary"] = strip_html(a.get("summary", ""))

print(f"articles: {len(articles)}", file=sys.stderr)

json.dump(articles, sys.stdout)
