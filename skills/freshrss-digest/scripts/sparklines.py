#!/usr/bin/env python3
"""Show per-feed article frequency as unicode sparklines.

Usage: sparklines.py <articles_json> [--days N] [--min N]

Input is the JSON output of load_articles.py or process_articles.py.
Each row shows a feed's posting rhythm over the last N days (default 30).
The sparkline is normalised per-feed so shape (rhythm) is visible regardless
of volume. Total unread count is shown on the right.

--days N    Number of days to cover (default 30)
--min N     Hide feeds with fewer than N articles in the window (default 1)
--top N     Only show the top N feeds by unread count
"""
import datetime
import json
import sys
from collections import defaultdict

BLOCKS = " ▁▂▃▄▅▆▇█"


def sparkline(values):
    hi = max(values) if values else 0
    if hi == 0:
        return " " * len(values)
    return "".join(BLOCKS[round(v / hi * (len(BLOCKS) - 1))] for v in values)


args = sys.argv[1:]
if not args:
    print(__doc__)
    sys.exit(1)

json_path = args[0]
days = 30
min_articles = 1
top = None

i = 1
while i < len(args):
    if args[i] == "--days" and i + 1 < len(args):
        days = int(args[i + 1])
        i += 2
    elif args[i] == "--min" and i + 1 < len(args):
        min_articles = int(args[i + 1])
        i += 2
    elif args[i] == "--top" and i + 1 < len(args):
        top = int(args[i + 1])
        i += 2
    else:
        i += 1

with open(json_path) as f:
    articles = json.load(f)

now = datetime.datetime.now()
start = now - datetime.timedelta(days=days)
start_ts = start.timestamp()

feed_buckets = defaultdict(lambda: [0] * days)
feed_total = defaultdict(int)

for a in articles:
    pub = a.get("published", 0)
    if pub < start_ts:
        continue
    day_offset = (datetime.datetime.fromtimestamp(pub).date() - start.date()).days
    if 0 <= day_offset < days:
        feed_buckets[a["feed_name"]][day_offset] += 1
        feed_total[a["feed_name"]] += 1

feeds = sorted(
    [(name, feed_total[name]) for name in feed_buckets if feed_total[name] >= min_articles],
    key=lambda x: -x[1],
)

if not feeds:
    print("No articles in window.")
    sys.exit(0)

if top is not None:
    feeds = feeds[:top]

name_width = min(max(len(name) for name, _ in feeds), 36)
header_spark = f"◄ {days}d ago" + " " * (days - 14) + "today ►"

print(f"{'Feed':<{name_width}}  {header_spark}  unread")
print("─" * (name_width + days + 10))

for name, total in feeds:
    spark = sparkline(feed_buckets[name])
    print(f"{name[:name_width]:<{name_width}}  {spark}  {total:>5}")
