#!/usr/bin/env python3
"""List feeds with unread article counts and sample titles.

Usage: list_feeds.py <filtered_json_path> [--sample N]

Default sample size is 2 titles per feed. Pass --sample 0 for counts only.
"""
import json
import sys
from collections import defaultdict

json_path = sys.argv[1]
sample_n = 2
if "--sample" in sys.argv:
    idx = sys.argv.index("--sample")
    sample_n = int(sys.argv[idx + 1])

with open(json_path) as f:
    articles = json.load(f)

feeds = defaultdict(list)
for a in sorted(articles, key=lambda x: -x["published"]):
    feeds[a["feed_name"]].append(a)

for feed, items in sorted(feeds.items(), key=lambda x: -len(x[1])):
    print(f"{len(items):3d}  {feed}")
    for a in items[:sample_n]:
        print(f"       · {a['title']}")
        print(f"         {a['url']}")
