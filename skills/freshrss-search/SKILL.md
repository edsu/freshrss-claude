---
name: freshrss-search
description: >-
  Search the user's unread FreshRSS articles for a specific topic, using
  semantic relevance over titles and summaries. Use when the user asks
  "what's in my feeds about X", "any news on X in my feeds", or invokes
  `/freshrss-search <topic>`. Requires the freshrss MCP server.
---

# Feed search

Semantically search the user's **unread** FreshRSS articles for a topic the user describes in free text, then surface the matches in a format that scales with hit count:

- **≤25 matches → Reading queue.** One linked bullet per match with a short framing phrase.
- **>25 matches → Curated TL;DR.** Themed prose grouping the matches under sub-topics, with bold lead-ins and inline links.

The skill does **not** apply a time window — it searches everything currently unread, on the assumption that if it's still unread, it's still in scope.

After presenting results, offer to drill deeper on a specific item by fetching its URL and summarizing the full article.

## When to use

- `/freshrss-search <topic>` (e.g. `/feed-search what's happening with Iran`, `/feed-search AI regulation`, `/feed-search local DC news`)
- "What's in my feeds about X?"
- "Any unread posts on X?"

## Arguments

`/freshrss-search` takes a **free-text topic phrase** as its argument. Interpret it as the user's topical intent — extract both literal keywords and the broader concept. Examples:

- `/freshrss-search Iran` → literal mentions of Iran, plus related (Israel/Gaza, US strikes, oil, sanctions)
- `/freshrss-search what's happening with the Supreme Court` → SCOTUS rulings, nominations, related legal news
- `/freshrss-search interesting AI critique` → not "anything about AI" but specifically critical or skeptical pieces

If `args` is empty, ask the user what topic they want to search for. Don't guess.

## Instructions

### 1. Fetch all unread articles

If the schema for `mcp__freshrss__get_unread_articles` isn't loaded yet:
`ToolSearch` with `select:mcp__freshrss__get_unread_articles`.

Call it with:
- `limit`: 2000 (the client pages internally via the Google Reader `continuation` token, so this is a per-call ceiling on results, not a per-HTTP-request cap)
- `max_summary_length`: 300
- **No** `since_timestamp` — we want everything unread

The result will almost certainly exceed the inline tool-result cap. The harness saves the full result to a file and shows a preview with a path. Note the path — you'll pass it to the script in step 2.

If `len(articles) == 2000` exactly, that's the saturation signal — there may be more unread than you're seeing. Note this to the user at the end and consider bumping `limit` higher.

### 2. Load and strip HTML

Run the loading script — it strips HTML from all summaries and outputs clean articles as JSON:

```bash
python skills/freshrss-search/scripts/load_articles.py "$path" > /tmp/freshrss_articles.json
```

Then load the result:

```python
import json
with open("/tmp/freshrss_articles.json") as f:
    articles = json.load(f)
```

### 3. Semantically filter against the topic

Read every article's title + cleaned summary and judge relevance to the user's topic phrase. **No server-side keyword pre-filter** — Claude does the matching, so semantically-adjacent items (e.g. "ICE detention center" for a "immigration policy" query) are caught even when the exact keyword is absent.

Be generous-but-honest:
- Include items that genuinely speak to the topic, even tangentially.
- **Exclude** items that merely mention a keyword in passing (e.g. "Iran" in a list of countries when the article is about something else).
- When the topic phrase implies a stance or angle ("critical AI takes", "good news"), respect it — don't return everything on the broader subject.

If the user's topic is vague or could mean multiple things, lean toward broader inclusion and let them refine.

### 4. Survey

Print `len(matches)` and a one-line note on the date range of matches and which feeds they came from. This sets expectations and tells you which mode to use.

### 5. Pick the mode and write the results

**Every item mentioned must be linked via inline markdown.**

#### Mode A — Reading queue (≤25 matches)

- Optionally cluster under light `###` sub-headings if there's a natural split (e.g. "US strikes" vs. "diplomatic angle"), but don't force it. A flat list is fine for narrow topics.
- One bullet per article: short framing phrase + linked title + feed name in parens.
- Order: most-relevant first (your judgment), or newest first if relevance is roughly equal.
- Don't drop matches in this mode — the user asked for everything on the topic.

#### Mode B — Curated TL;DR (>25 matches)

- `###` heading per sub-theme within the topic. Bulleted items with **bold lead-ins**. One sentence per bullet, occasionally two.
- Aim to name roughly **⅔ of matches** (higher than `/feed-digest`'s ⅓ — the user explicitly asked about this topic, so coverage matters more than ruthless curation).
- Still drop obvious filler (sponsored posts, duplicate coverage of the same news event from multiple feeds — collapse those: "covered by NYT, Maryland Matters, and Drop Site").
- For dense single-feed clusters on this topic, pick 2–3 representatives and add "and N more from [feed]".

### 6. Offer drill-deeper

After the results, end with a one-liner like:

> Want me to pull the full text of any of these and go deeper?

If the user picks one, use `WebFetch` (load via `ToolSearch` with `select:WebFetch` if needed) against the article URL and summarize the full piece. The skill itself stops at presenting results — drill-deeper is a follow-on action triggered by the user.

### 7. No-matches fallback

If the semantic filter returns **zero** unread matches, don't just say "nothing found." Offer to broaden:

> Nothing matching "{topic}" in your unread feeds. Want me to search read articles too?

If yes, load `mcp__freshrss__search_articles` via `ToolSearch` and call it with the user's topic phrase (or a keyword extracted from it) as the query. Present those results in the same mode-A/mode-B format. Note in the output that these are previously-read articles.

If matches are very sparse (1–3 items) but exist, present them and add the same offer to broaden — sparse matches often signal a slightly-too-narrow read of the topic.

## Notes

- The freshrss MCP server returns structured JSON since the `tools-json-output-and-since-timestamp` branch — no `ast.literal_eval` needed.
- This skill produces a chat-only result — no file writes unless asked.
- Unlike `/freshrss-digest`, this skill does **not** offer mark-as-read by default. Topic-search matches are usually things the user *wants* to read; clearing them would be counterproductive. If the user explicitly asks to mark them read or to star them, do so via `mcp__freshrss__mark_as_read` or `mcp__freshrss__star_article`.
