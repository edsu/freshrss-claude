# freshrss-claude

> **Experimental.** This is a personal project for exploring MCP server development and Claude plugin/skill building. It works, but expect rough edges and breaking changes.

A Claude Code plugin that connects Claude to your [FreshRSS](https://freshrss.org/) feeds. It bundles an MCP server (wrapping the FreshRSS Google Reader API) and four skills for digesting, searching, and catching up on your subscriptions.

Token-optimized: the server returns only essential fields with configurable summary truncation, achieving ~90% reduction vs raw RSS XML payloads.

The MCP server (`src/freshrss_mcp/`) is based on [ChrisLAS/freshrss-mcp](https://github.com/ChrisLAS/freshrss-mcp), originally built for Streamable HTTP transport and the OpenClaw gateway. This repo restructures it as a Claude Code plugin (stdio transport, plugin manifest, bundled skills).

---

## Install

### Prerequisites

[`uv`](https://docs.astral.sh/uv/getting-started/installation/) (Python 3.12+) must be installed — the plugin uses `uv run freshrss-mcp` to start the bundled MCP server.

### Steps

**1. Register this GitHub repo as a plugin marketplace** (run in your terminal):

```bash
claude plugin marketplace add https://github.com/edsu/freshrss-claude
```

This tells Claude Code to treat this repository as a source of plugins. Claude Code fetches the plugin manifest from the repo and assigns the marketplace the name `freshrss-claude-marketplace`.

**2. Install the plugin** (run in your terminal):

```bash
claude plugin install freshrss-claude
```

This installs the `freshrss-claude` plugin from the marketplace you just registered.

**3. Configure your FreshRSS credentials** (run inside Claude Code):

```
/plugin configure freshrss-claude@freshrss-claude-marketplace
```

The `@freshrss-claude-marketplace` suffix tells Claude Code which marketplace the plugin came from — this disambiguates in case you have multiple marketplaces with plugins of the same name. You'll be prompted for:

- **FreshRSS URL** — base URL of your instance, e.g. `https://freshrss.example.com`
- **FreshRSS username**
- **FreshRSS API password** — from FreshRSS under Settings → Profile → API Management (this is separate from your login password)

**4. Reload plugins** (run inside Claude Code):

```
/reload-plugins
```

The MCP server starts automatically from that point — there's nothing else to run.

---

## Skills

The `skills/` directory ships four skills that drive the bundled `freshrss` MCP server:

- **`freshrss-digest`** — `/freshrss-digest [timeframe]` produces a digest of recent unread articles (e.g. `3d`, `last week`). Auto-switches between a reading-queue index (≤25 posts) and a themed TL;DR (>25 posts), and offers to mark the window as read when done.
- **`freshrss-search`** — `/freshrss-search <topic>` semantically searches all unread articles for a topic (e.g. `Iran`, `interesting AI critique`). Same adaptive output format, with an offer to drill into individual results.
- **`freshrss-category`** — `/freshrss-category <category> [timeframe]` summarizes recent posts from any FreshRSS category. For the "People" category it's person-centric (one paragraph per person, warm catch-up tone); for other categories it's one paragraph per active feed.
- **`freshrss-subscriptions`** — `/freshrss-subscriptions [timeframe]` lists which feeds have unread articles in a window, with counts and sample titles, sorted by volume.

All four skills are installed automatically with the plugin — no separate symlinking step.

---

## Example: summarize the last two days

Inside Claude Code, run:

```
/freshrss-digest 2d
```

Claude fetches your unread articles from the past 48 hours and produces a digest. With fewer than 25 posts it renders a grouped reading-queue index (every article linked); with more it switches to a curated TL;DR that highlights roughly a third of them by theme and drops filler:

```
### Technology
- **New LLM benchmarks published** — Stanford HELM adds five new tasks targeting reasoning and long-context recall. ([link](…)) — *AI Weirdness*
- **Firefox 128 ships** — Tab Groups and a reworked reader mode land in stable. ([link](…)) — *Mozilla Hacks*

### Politics
- Local city council approved the transit funding amendment after two hours of public comment. ([link](…)) — *DCist*

…

Mark all 47 articles in this window as read in FreshRSS? (yes/no)
```

After the digest Claude offers to mark everything in that window as read in FreshRSS.

---

## MCP Tools

The bundled server exposes these tools:

| Tool | Description | Key Args |
|------|-------------|----------|
| `get_unread_articles` | Fetch unread articles with filtering | `limit`, `feed_ids`, `since_timestamp`, `max_summary_length` |
| `get_articles_by_feed` | Articles from a specific feed | `feed_id`, `limit`, `include_read` |
| `search_articles` | Client-side keyword search in titles/summaries | `query`, `limit`, `feed_ids` |
| `list_feeds` | All subscribed feeds with unread counts | — |
| `get_feed_info` | Detailed info for one feed | `feed_id` |
| `get_feed_stats` | Statistics for all feeds | — |
| `mark_as_read` | Batch mark articles as read | `article_ids` |
| `mark_as_unread` | Batch mark articles as unread | `article_ids` |
| `star_article` | Star/favorite an article | `article_id` |
| `unstar_article` | Remove star from an article | `article_id` |

---

## Architecture Notes

- **Transport**: stdio. Claude Code spawns the bundled server as a subprocess via `.mcp.json`.
- **Auth**: Lazy authentication — the FreshRSS client authenticates on the first API call, not at startup.
- **Error handling**: Every tool catches all exceptions and returns `"Error: ..."` strings. The MCP protocol never sees uncaught exceptions.
- **Config**: pydantic-settings `BaseSettings` with `SecretStr` for the password, sourced from the plugin's `userConfig`.
- **Dependencies**: `fastmcp`, `httpx`, `pydantic-settings`. No version pins.
- **Tests**: unit tests covering config, client, tools, and models. Run with `uv run pytest -v`.

### Project Structure

```
.claude-plugin/plugin.json   — plugin manifest (userConfig: URL, username, password)
.mcp.json                    — bundled MCP server definition (stdio)
skills/
  freshrss-digest/
  freshrss-search/
  freshrss-category/
  freshrss-subscriptions/
src/freshrss_mcp/
  server.py    — FastMCP entry point (stdio transport)
  tools.py     — MCP tool definitions with error boundaries
  client.py    — Async FreshRSS Google Reader API client (httpx)
  config.py    — pydantic-settings config from env vars
  models.py    — Article and Feed dataclasses
tests/
  test_config.py   — Config validation, defaults, secret masking
  test_client.py   — Auth, feeds, articles, ID extraction
  test_tools.py    — Tool happy paths + error boundaries
  test_models.py   — Serialization, construction, edge cases
```

## Development

```bash
git clone https://github.com/edsu/freshrss-claude.git
cd freshrss-claude
uv sync
uv run pytest -v

# Run the server directly for debugging (stdio — expects an MCP client on the other end)
export FRESHRSS_URL="https://freshrss.example.com"
export FRESHRSS_USERNAME="youruser"
export FRESHRSS_PASSWORD="yourpass"
uv run freshrss-mcp
```

### Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `FRESHRSS_URL` | Yes | — | FreshRSS instance URL |
| `FRESHRSS_USERNAME` | Yes | — | FreshRSS username |
| `FRESHRSS_PASSWORD` | Yes | — | FreshRSS API password |
| `FRESHRSS_API_PATH` | No | `/api/greader.php` | Google Reader API path |

## Known Limitations

- **Client-side search**: FreshRSS API lacks server-side search; `search_articles` fetches articles then filters locally.
- **No pagination**: Article fetches use a single `limit` parameter without cursor-based pagination.
- **No real-time updates**: The server is request-driven; no push/webhook mechanism for new articles.

## License

MIT
