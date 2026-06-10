---
name: freshrss-subscriptions
description: >-
  List the user's FreshRSS subscriptions that have unread articles in a given
  timeframe, with counts and sample titles. Use when the user asks "which feeds
  have new posts?", "what subscriptions are active this week?", or invokes
  `/freshrss-subscriptions`. Requires the freshrss MCP server.
---

# Feed subscriptions

List which FreshRSS feeds have unread articles in a given window, with unread
counts and a couple of sample titles per feed, sorted by volume.

## When to use

- "Which feeds have new posts this week?"
- "What subscriptions are active today?"
- "Show me what feeds have unread articles"
- Invoked as `/freshrss-subscriptions` (with or without a time argument)

## Arguments

Takes an optional free-text time-frame argument. Examples:

- `/freshrss-subscriptions` → default 7 days
- `/freshrss-subscriptions 1d` / `24h` / `yesterday` / `3d` / `2w` / `last month`

If `args` is empty, use **7 days**.

## Instructions

### 1. Compute the cutoff timestamp

```bash
# macOS
date -v-7d +%s

# Linux
date -d '7 days ago' +%s
```

### 2. Fetch unread articles

If `mcp__freshrss__get_unread_articles` schema isn't loaded:
`ToolSearch` with `select:mcp__freshrss__get_unread_articles`.

Call with:
- `since_timestamp`: cutoff from step 1
- `limit`: 2000
- `max_summary_length`: 0  (summaries not needed for this skill)

The result will likely exceed the inline cap and be saved to a file. Note the path.

### 3. Filter and process

```bash
python skills/freshrss-digest/scripts/process_articles.py "$path" "$cutoff" > /tmp/freshrss_filtered.json
```

### 4. List feeds

```bash
python skills/freshrss-subscriptions/scripts/list_feeds.py /tmp/freshrss_filtered.json
```

This prints each feed sorted by unread count, with up to 2 sample article titles
and URLs per feed. Pass `--sample 0` to show counts only.

### 5. Present the results

Format the output as a clean list. Use the feed names as section labels or a
simple table. Keep it scannable — the goal is a quick overview, not a digest.

If `len(all_articles) > len(recent)` (process_articles.py stderr shows
"filtered from N"), add a one-line note that the counts only reflect articles
published within the window.

## Notes

- This skill does not offer mark-as-read — it's a read-only overview.
- For a full narrative digest, use `/freshrss-digest`.
- For searching within feeds, use `/freshrss-search`.
