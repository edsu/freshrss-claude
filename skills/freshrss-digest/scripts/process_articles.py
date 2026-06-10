#!/usr/bin/env python3
"""Load, filter, and strip articles from a saved MCP result file.

Usage: process_articles.py <json_path> <cutoff_timestamp> [--category NAME --feeds-json PATH]

Outputs filtered articles as JSON to stdout. Survey info goes to stderr.
"""
import argparse
import html
import json
import re
import sys
from collections import Counter
from datetime import datetime


def strip_html(s):
    s = re.sub(r"<[^>]+>", "", s or "")
    s = html.unescape(s)
    return re.sub(r"\s+", " ", s).strip()


parser = argparse.ArgumentParser()
parser.add_argument("json_path")
parser.add_argument("cutoff_ts", type=int)
parser.add_argument("--category", default=None)
parser.add_argument("--feeds-json", default=None)
args = parser.parse_args()

json_path, cutoff_ts = args.json_path, args.cutoff_ts

category_feeds = None
if args.category:
    if not args.feeds_json:
        print("--feeds-json required when --category is set", file=sys.stderr)
        sys.exit(1)
    with open(args.feeds_json) as f:
        feeds_data = json.load(f)
    category_feeds = {
        feed["name"]
        for feed in feeds_data.get("result", [])
        if args.category in (feed.get("categories") or [])
    }

with open(json_path) as f:
    data = json.load(f)
all_articles = data["result"]

filtered = [a for a in all_articles if a.get("published", 0) >= cutoff_ts]
if category_feeds is not None:
    filtered = [a for a in filtered if a.get("feed_name") in category_feeds]

for a in filtered:
    a["summary"] = strip_html(a.get("summary", ""))

counts = Counter(a["feed_name"] for a in filtered)
if filtered:
    dates = [a["published"] for a in filtered]
    date_range = (
        f"{datetime.fromtimestamp(min(dates)).date()} – "
        f"{datetime.fromtimestamp(max(dates)).date()}"
    )
else:
    date_range = "no articles"

print(f"articles: {len(filtered)} (filtered from {len(all_articles)})", file=sys.stderr)
print(f"date range: {date_range}", file=sys.stderr)
for feed, count in counts.most_common(10):
    print(f"  {count:3d}  {feed}", file=sys.stderr)

json.dump(filtered, sys.stdout)
