---
name: freshrss-digest
description: >-
  Produce a digest of recent unread articles from the user's FreshRSS feeds.
  Use when the user asks for a digest of their feeds, "what's new in my feeds",
  "summarize the posts from the last N days/week", or invokes `/freshrss-digest`.
  Requires the freshrss MCP server.
---

# Feed digest

Produce a summary of recent unread articles from FreshRSS. The format depends on **how many articles** fall in the window:

- **≤25 posts → Reading queue.** A loosely topic-grouped index where every post is listed and linked.
- **>25 posts → Curated TL;DR.** Themed prose with selective coverage. Target roughly ⅓ of input items by name; aggressively drop filler and condense single-feed clusters.

After the digest, offer to mark all articles in the window as read.

## When to use

- "Summarize the posts from the last week"
- "What's new in my feeds?"
- "Give me a digest of the last N days"
- Invoked as `/freshrss-digest` (with or without a time argument)

## Arguments

`/freshrss-digest` takes an optional free-text time-frame argument. Examples:

- `/freshrss-digest` → default 7 days
- `/freshrss-digest 3d` / `3 days` / `last week` / `24h` / `yesterday` / `2w` / `last month`

If `args` is empty, use **7 days**.

## Instructions

### 1. Compute the cutoff timestamp

Parse the argument to a duration and shell out for the timestamp — don't compute by hand:

```bash
# macOS
date -v-7d +%s         # 7 days ago
date -v-24H +%s        # 24 hours ago
date -v-2w +%s         # 2 weeks ago

# Linux
date -d '7 days ago' +%s
```

Remember the window size — you'll reuse it in step 3.

### 2. Fetch the articles

If the schema for `mcp__freshrss__get_unread_articles` isn't loaded yet:
`ToolSearch` with `select:mcp__freshrss__get_unread_articles`.

Call it with:
- `since_timestamp`: the value from step 1
- `limit`: 2000 (the client pages internally via the Google Reader `continuation` token, so this is a per-call ceiling on results, not a per-HTTP-request cap)
- `max_summary_length`: 300

A week of feeds usually exceeds the inline tool-result cap (~25KB). The harness saves the full result to a file and shows a preview with a path. Note the path — you'll pass it to the script in step 3.

Do **not** retry with a smaller `limit` to fit inline — you'll just get fewer articles. If the script reports "filtered from 2000" exactly, that's the saturation signal: there may be more in the window than you're seeing, and you should either bump `limit` higher or warn the user.

### 3. Filter, survey, and strip HTML

Run the processing script — it filters by `published` (not crawl time), prints a top-10 survey to stderr, and outputs filtered+stripped articles as JSON:

```bash
python skills/freshrss-digest/scripts/process_articles.py "$path" "$cutoff" > /tmp/freshrss_filtered.json
```

Then get the full per-feed breakdown:

```bash
python skills/freshrss-digest/scripts/survey_articles.py /tmp/freshrss_filtered.json
```

To browse article titles, URLs, and summaries (grouped by feed, or `--by-time` for chronological):

```bash
python skills/freshrss-digest/scripts/list_articles.py /tmp/freshrss_filtered.json
```

Use the survey output to:
- Decide which mode to use (≤25 or >25)
- Spot dense single-feed clusters early
- Confirm whether `ot` leaked older articles (stderr from process_articles.py shows "filtered from N")

### 6. Pick the mode and write the digest

**Every item mentioned by name must include its URL via inline markdown links.**

#### Mode A — Reading queue (≤25 posts)

Goal: a navigable index. Every post appears, every post is linked.

- Light thematic grouping under `###` headings (Politics, AI/tech, Local, Music, etc.). Use whatever buckets fit the data — don't force categories.
- Within each group, one bullet per article: a short framing phrase + the article title as a markdown link, plus the feed name.
- Order within a group: newest first, or whatever reads naturally.
- Don't omit anything; this mode trusts the user's subscriptions.

#### Mode B — Curated TL;DR (>25 posts)

Goal: signal. Aim to mention roughly **⅓ of `len(recent)`** by name (e.g. 100 posts → ~33 items; 60 → ~20). The rest are silently dropped.

- `###` heading per theme. Bulleted items with **bold lead-ins**. One sentence per bullet, occasionally two.
- **Inline-link every referenced article.** For multi-article bullets, link each source/title fragment inline rather than dumping URL lists.
- **Dense clusters** (one feed contributing ≥6 posts): pick 2–3 representatives, link them, then add "and N more in [feed name]" — do not enumerate the rest.
- **Drop filler** without comment:
  - Sponsored / advertorial posts
  - Daily crime blotters / police logs
  - "Books received" / "currently reading" digests
  - Sub-100-word link-out posts that just point elsewhere
  - Job postings, store-opening announcements
  - Forum-issue trackers (e.g. dense Kagi-feedback threads) — at most one or two representative items, even if there are 12
- The summary is the deliverable. If the reader wants the full list, they can open their RSS reader.

### 7. Caveat if `ot` leaked

If `len(articles) > len(recent)` — i.e., client-side filtering had to discard articles older than the window — add a one-line note at the bottom of the digest.

### 8. Offer mark-as-read

After printing the digest, ask the user if they want to mark the items as read. The offered scope is **everything in the window** — all `recent` article IDs, whether or not they appeared in the digest by name.

Use `AskUserQuestion` with a simple yes/no, or just ask in plain prose. Example phrasing:

> Mark all N articles in this window as read in FreshRSS?

If yes, call `mcp__freshrss__mark_as_read` with `article_ids=[a["id"] for a in recent]` (load the schema first via `ToolSearch` if needed). The tool now returns `{"ok": true}` on success; confirm to the user.

If the user says no or doesn't respond clearly, leave the items unread.

## Notes

- The freshrss MCP server returns structured JSON (no `ast.literal_eval` needed) since the `tools-json-output-and-since-timestamp` branch.
- For digests longer than ~1 week, the 100-article ceiling will bite. Acknowledge the truncation explicitly, or page through `since_timestamp` windows.
- This skill produces a chat-only digest — it does not write files. If the user wants an archival snapshot, they can ask for one separately.
