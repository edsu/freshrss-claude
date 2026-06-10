#!/usr/bin/env python3
"""Print articles grouped by feed with clean display names.

Usage: show_feeds.py <filtered_json_path>

Outputs one section per feed, sorted by post count descending, with full
summaries. Designed to be read before writing a category summary.
"""
import json
import re
import sys
from collections import defaultdict


def display_name(feed_name):
    """Extract a readable person name from a feed name."""
    # "@handle.bsky.social - Real Name" → "Real Name"
    m = re.match(r"@\S+\s+-\s+(.+)", feed_name)
    if m:
        return m.group(1)
    # "Name on Bluesky" → "Name"
    name = re.sub(r"\s+on Bluesky$", "", feed_name, flags=re.IGNORECASE)
    # "Name's blog" / "Name's notes" → "Name"
    name = re.sub(r"'s\s+(blog|notes|website|journal|newsletter).*$", "", name, flags=re.IGNORECASE)
    return name.strip()


with open(sys.argv[1]) as f:
    articles = json.load(f)

by_feed = defaultdict(list)
for a in articles:
    by_feed[a["feed_name"]].append(a)

# Sort by post count descending, then alphabetically
for feed_name, posts in sorted(by_feed.items(), key=lambda x: (-len(x[1]), display_name(x[0]))):
    name = display_name(feed_name)
    label = name if name == feed_name else f"{name}  ({feed_name})"
    print(f"=== {label} — {len(posts)} post{'s' if len(posts) != 1 else ''} ===")
    for a in sorted(posts, key=lambda x: -x["published"]):
        print(f"  {a['title']}")
        print(f"  {a['url']}")
        if a.get("summary"):
            print(f"  {a['summary']}")
    print()
