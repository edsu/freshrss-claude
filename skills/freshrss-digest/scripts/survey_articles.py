#!/usr/bin/env python3
"""Print a full per-feed breakdown of a filtered articles JSON file.

Usage: survey_articles.py <filtered_json_path>

Input is the JSON output of process_articles.py (a list of article dicts).
"""
import json
import sys
from collections import Counter

json_path = sys.argv[1]

with open(json_path) as f:
    articles = json.load(f)

feeds = Counter(a["feed_name"] for a in articles)
print(f"Total: {len(articles)}")
for feed, count in feeds.most_common():
    print(f"  {count:3d}  {feed}")
