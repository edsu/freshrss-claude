---
name: freshrss-people
description: >-
  Summarize recent posts from the FreshRSS "People" category — feeds from
  individual people the user follows. Treats each person as an individual,
  summarizing their recent interests and thoughts with links. Use when the user
  asks "what are the people I follow up to?", "what's new from people in my
  feeds?", or invokes `/freshrss-people`. Requires the freshrss MCP server.
---

# People digest

Summarize recent posts from the FreshRSS **People** category. Unlike a regular
feed digest, this is person-centric: for each active person, write a short
paragraph about what they've been thinking about, writing, or sharing — with
inline links to the posts. The goal is to feel like a catch-up with people you
follow, not a link list.

## When to use

- "What are the people I follow up to?"
- "What's new from people in my feeds?"
- Invoked as `/freshrss-people` (with or without a time argument)

## Arguments

Takes an optional free-text time-frame argument. Examples:

- `/freshrss-people` → default 7 days
- `/freshrss-people 1d` / `24h` / `yesterday` / `3d` / `2w` / `last month`

If `args` is empty, use **7 days**.

## Instructions

### 1. Compute the cutoff timestamp

```bash
# macOS
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

### 4. Filter to People feeds

```bash
python skills/freshrss-digest/scripts/process_articles.py \
  "$articles_path" "$cutoff" \
  --category People \
  --feeds-json "$feeds_path" \
  > /tmp/freshrss_people.json
```

The script prints a per-person post count survey to stderr — check it to see
who's been active before writing.

### 5. Read the articles

```bash
python skills/freshrss-people/scripts/show_people.py /tmp/freshrss_people.json
```

This groups articles by person with cleaned-up display names and full summaries.
Read through all of it before writing — the goal is to understand what each
person is actually saying, not just headline-scan.

### 6. Write the person-centric summary

One paragraph per active person, ordered by post count (most active first).

- **Lead with the person's name** (use the clean display name from the script,
  not the raw feed handle).
- **Synthesize** across their posts if they have multiple — what's the thread or
  mood? Don't just list each post sequentially.
- **Inline-link** to specific posts naturally within the prose. Don't append
  URLs at the end.
- **Tone**: warm and conversational — this is a catch-up, not a news brief.
- If someone only posted a link or a short reaction, say what it was about and
  why it seemed to matter to them.
- Skip people with no posts in the window without mentioning them.
- Do **not** group by topic across people — keep each person together.

### 7. Offer mark-as-read

After the summary, ask the user if they'd like to mark all People articles as
read. Load `mcp__freshrss__mark_as_read` via ToolSearch if needed, then call it
with the article IDs from the filtered JSON:

```python
import json
people_articles = json.load(open("/tmp/freshrss_people.json"))
article_ids = [a["id"] for a in people_articles]
```

The tool returns `{"ok": true}` on success; confirm to the user.

## Notes

- The "People" category label is case-sensitive — use `People`, not `people`.
- `process_articles.py --category` requires `--feeds-json` pointing at the
  saved `list_feeds` output.
- If the feeds list came back inline (rare, small subscriber count), save it:
  `echo '$result' > /tmp/freshrss_feeds.json` then pass that path.
- For a broader topic-based digest across all feeds, use `/freshrss-digest`.
- For searching within People feeds, use `/freshrss-search`.
