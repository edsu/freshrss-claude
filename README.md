# freshrss-cowork

> **Experimental.** This is a personal project for exploring MCP server development and Claude plugin/skill building. It works, but expect rough edges and breaking changes.

A Claude Cowork plugin that connects Claude to your [FreshRSS](https://freshrss.org/) feeds. It bundles an MCP server (wrapping the FreshRSS Google Reader API) and four skills for digesting, searching, and catching up on your subscriptions.

Token-optimized: the server returns only essential fields with configurable summary truncation, achieving ~90% reduction vs raw RSS XML payloads.

The MCP server (`src/freshrss_mcp/`) is based on [ChrisLAS/freshrss-mcp](https://github.com/ChrisLAS/freshrss-mcp), originally built for Streamable HTTP transport and the OpenClaw gateway. This repo restructures it as a Cowork plugin (stdio transport, plugin manifest, bundled skills).

---

## Install

### Prerequisites

- [`uv`](https://docs.astral.sh/uv/getting-started/installation/) (Python 3.12+) must be installed on the machine running Cowork — the plugin invokes `uv run freshrss-mcp` to start the bundled MCP server. `uv` is not bundled with Cowork, so install it first if you don't already have it.

### Steps

1. Add this repo as a plugin in Cowork (or Claude Code: `claude plugin install` / via a marketplace entry pointing at this repo).
2. When prompted, enter your FreshRSS connection details:
   - **FreshRSS URL** — base URL of your instance, e.g. `https://freshrss.example.com`
   - **FreshRSS username**
   - **FreshRSS API password** — from FreshRSS under Settings → Profile → API Management (this is a separate password from your login password unless you've set them the same)

These are stored securely (the password goes to the system keychain) and passed to the bundled MCP server, which Cowork starts automatically — there's nothing to run yourself, beyond installing `uv`.

---

## Skills

The `skills/` directory ships four skills that drive the bundled `freshrss` MCP server:

- **`freshrss-digest`** — `/freshrss-digest [timeframe]` produces a digest of recent unread articles (e.g. `3d`, `last week`). Auto-switches between a reading-queue index (≤25 posts) and a themed TL;DR (>25 posts), and offers to mark the window as read when done.
- **`freshrss-search`** — `/freshrss-search <topic>` semantically searches all unread articles for a topic (e.g. `Iran`, `interesting AI critique`). Same adaptive output format, with an offer to drill into individual results.
- **`freshrss-category`** — `/freshrss-category <category> [timeframe]` summarizes recent posts from any FreshRSS category. For the "People" category it's person-centric (one paragraph per person, warm catch-up tone); for other categories it's one paragraph per active feed.
- **`freshrss-subscriptions`** — `/freshrss-subscriptions [timeframe]` lists which feeds have unread articles in a window, with counts and sample titles, sorted by volume.

All four skills are installed automatically with the plugin — no separate symlinking step.

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

- **Transport**: stdio. Cowork/Claude Code spawn the bundled server as a subprocess via `.mcp.json`.
- **Auth**: Lazy authentication — the FreshRSS client authenticates on the first API call, not at startup.
- **Error handling**: Every tool catches all exceptions and returns `"Error: ..."` strings. The MCP protocol never sees uncaught exceptions.
- **Config**: pydantic-settings `BaseSettings` with `SecretStr` for the password, sourced from the plugin's `userConfig`.
- **Dependencies**: `fastmcp`, `httpx`, `pydantic-settings`. No version pins.
- **Tests**: unit tests covering config, client, tools, and models. Run with `uv run pytest -v`.

### Project Structure

```
.claude-plugin/plugin.json   — Cowork plugin manifest (userConfig: URL, username, password)
.mcp.json                     — bundled MCP server definition (stdio)
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
git clone https://github.com/edsu/freshrss-cowork.git
cd freshrss-cowork
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
