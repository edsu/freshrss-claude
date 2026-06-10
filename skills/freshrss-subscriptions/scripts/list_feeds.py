#!/usr/bin/env python3
"""List feeds with unread article counts and activity bars.

Usage: list_feeds.py <filtered_json_path> [--sample N] [--no-bars]

Default sample size is 2 titles per feed. Pass --sample 0 for counts only.
Pass --no-bars to suppress the activity bars.
"""
import json
import sys
from collections import defaultdict

json_path = sys.argv[1]
sample_n = 2
show_bars = True

if "--sample" in sys.argv:
    idx = sys.argv.index("--sample")
    sample_n = int(sys.argv[idx + 1])
if "--no-bars" in sys.argv:
    show_bars = False

with open(json_path) as f:
    articles = json.load(f)

feeds = defaultdict(list)
for a in sorted(articles, key=lambda x: -x["published"]):
    feeds[a["feed_name"]].append(a)

sorted_feeds = sorted(feeds.items(), key=lambda x: -len(x[1]))

if not sorted_feeds:
    print("No feeds with unread articles in this window.")
    sys.exit(0)

max_count = len(sorted_feeds[0][1])
name_width = min(max(len(name) for name, _ in sorted_feeds), 32)
BAR_WIDTH = 20

for feed, items in sorted_feeds:
    count = len(items)
    if show_bars:
        filled = round(count / max_count * BAR_WIDTH) if max_count else 0
        bar = "█" * filled
        print(f"{feed[:name_width]:<{name_width}}  {bar:<{BAR_WIDTH}}  {count:3d}")
    else:
        print(f"{count:3d}  {feed}")
    for a in items[:sample_n]:
        print(f"  · {a['title']}")
        print(f"    {a['url']}")
