#!/usr/bin/env python3
"""Print all articles from a filtered articles JSON file, grouped by feed.

Usage: list_articles.py <filtered_json_path> [--by-time]

Default: sorted by feed name, then newest first within each feed.
--by-time: sorted newest first across all feeds (ignores feed grouping).
"""
import json
import sys

json_path = sys.argv[1]
by_time = "--by-time" in sys.argv

with open(json_path) as f:
    articles = json.load(f)

if by_time:
    sorted_articles = sorted(articles, key=lambda x: -x["published"])
else:
    sorted_articles = sorted(articles, key=lambda x: (x["feed_name"], -x["published"]))

for a in sorted_articles:
    print(f"[{a['feed_name']}] {a['title']}")
    print(f"  url: {a['url']}")
    if a.get("summary"):
        print(f"  summary: {a['summary'][:200]}")
    print()
