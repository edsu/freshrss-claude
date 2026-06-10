---
name: freshrss-category
description: >-
  Summarize recent posts from a named FreshRSS category. For the "People"
  category, writes a person-centric narrative (one paragraph per person); for
  other categories, writes one paragraph per active feed. Use when the user asks
  "what's new in my <category> feeds?", "catch me up on <category>", or invokes
  `/freshrss-category <category>`. Requires the freshrss MCP server.
---

# Category digest

Summarize recent unread posts from a specific FreshRSS category. For the
**People** category, the output is person-centric: one paragraph per active
person, written like a catch-up with someone you follow. For any other category,
write one paragraph per active feed — what's the thread or mood of that feed
this week?

## When to use

- "What's new in my People feeds?"
- "Catch me up on Tech"
- Invoked as `/freshrss-category <category>` (with optional timeframe)

## Arguments

`<category> [timeframe]`

- `category` — the FreshRSS category name (case-sensitive, e.g. `People`, `Tech`, `News`)
- `timeframe` — optional, defaults to **7 days** (e.g. `1d`, `3d`, `2w`, `last month`)

## Instructions

### 1. Parse arguments and compute cutoff timestamp

Extract `category` (first token) and `timeframe` (remainder, default `7d`) from
`args`.

```bash
# macOS — substitute the parsed timeframe, e.g. for 7d:
date -v-7d +%s

# Linux
date -d '7 days ago' +%s
```

### 2. Fetch the feeds list

If `mcp__freshrss__list_feeds` schema isn't loaded:
`ToolSearch` with `select:mcp__freshrss__list_feeds`.

Call it (no arguments). The result is usually large and will be saved to a file
— note the path. This gives you feed names with their FreshRSS categories.

### 3. Fetch unread articles

If `mcp__freshrss__get_unread_articles` schema isn't loaded:
`ToolSearch` with `select:mcp__freshrss__get_unread_articles`.

Call with:
- `since_timestamp`: cutoff from step 1
- `limit`: 2000
- `max_summary_length`: 300

Note the saved file path.

### 4. Filter to the target category

```bash
python skills/freshrss-digest/scripts/process_articles.py \
  "$articles_path" "$cutoff" \
  --category "$category" \
  --feeds-json "$feeds_path" \
  > /tmp/freshrss_category.json
```

The script prints a per-feed post count survey to stderr — check it to see
who's been active before writing.

### 4b. Print the stats header

```bash
python skills/freshrss-digest/scripts/stats_header.py /tmp/freshrss_category.json "category · {category} · {timeframe}"
```

Include this output verbatim at the top of your response.

### 5. Read the articles

```bash
python skills/freshrss-category/scripts/show_feeds.py /tmp/freshrss_category.json
```

This groups articles by feed with cleaned-up display names and full summaries.
Read through all of it before writing.

### 6. Write the summary

**If category is `People`:** one paragraph per active person, ordered by post
count (most active first).

- Lead with the person's name (use the clean display name from the script).
- Synthesize across their posts — what's the thread or mood?
- Inline-link to specific posts naturally within the prose.
- Tone: warm and conversational — this is a catch-up, not a news brief.
- If someone only posted a link or a short reaction, say what it was about and
  why it seemed to matter to them.

**For any other category:** one paragraph per active feed, ordered by post count.

- Lead with the feed name.
- Summarize the week's posts for that feed — what topics, what angle?
- Inline-link to notable posts.
- Tone can be more neutral/informational than for People.

In both cases:
- Skip feeds/people with no posts in the window without mentioning them.
- Do **not** group by topic across feeds — keep each feed/person together.

### 7. Offer mark-as-read

After the summary, ask the user if they'd like to mark all articles in the
category as read. Load `mcp__freshrss__mark_as_read` via ToolSearch if needed,
then call it with the article IDs from the filtered JSON:

```python
import json
articles = json.load(open("/tmp/freshrss_category.json"))
article_ids = [a["id"] for a in articles]
```

The tool returns `{"ok": true}` on success; confirm to the user.

## Notes

- Category names are case-sensitive — use the exact name as it appears in
  FreshRSS (e.g. `People`, not `people`).
- `process_articles.py --category` requires `--feeds-json` pointing at the
  saved `list_feeds` output.
- If the feeds list came back inline (rare, small subscriber count), save it to
  a temp file and pass that path.
- For a broader digest across all feeds, use `/freshrss-digest`.
- For searching within a category, use `/freshrss-search`.
