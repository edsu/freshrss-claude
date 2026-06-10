#!/usr/bin/env python3
"""Print a bordered stats header for FreshRSS skill output.

Usage:
    stats_header.py <json_path> <label>
    stats_header.py --articles N --feeds N <label>

Examples:
    stats_header.py /tmp/freshrss_filtered.json "digest · 2d"
    stats_header.py --articles 8 --feeds 5 "search · Iran"
"""
import json
import sys


def render(label, n_articles, n_feeds):
    top_content = f"─ FreshRSS · {label} "
    stats_content = (
        f"  {n_articles} article{'s' if n_articles != 1 else ''}"
        f"  ·  {n_feeds} feed{'s' if n_feeds != 1 else ''}  "
    )
    inner = max(len(top_content) + 2, len(stats_content))
    print(f"┌{top_content}{'─' * (inner - len(top_content))}┐")
    print(f"│{stats_content}{' ' * (inner - len(stats_content))}│")
    print(f"└{'─' * inner}┘")


args = sys.argv[1:]

if "--articles" in args and "--feeds" in args:
    a_idx = args.index("--articles")
    f_idx = args.index("--feeds")
    n_articles = int(args[a_idx + 1])
    n_feeds = int(args[f_idx + 1])
    flags = {"--articles", args[a_idx + 1], "--feeds", args[f_idx + 1]}
    label = " ".join(a for a in args if a not in flags)
else:
    if not args:
        print(__doc__)
        sys.exit(1)
    json_path = args[0]
    label = " ".join(args[1:]) if len(args) > 1 else "FreshRSS"
    with open(json_path) as f:
        articles = json.load(f)
    n_articles = len(articles)
    n_feeds = len({a["feed_name"] for a in articles})

render(label, n_articles, n_feeds)
