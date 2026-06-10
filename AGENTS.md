# Agent Instructions

This project uses **bd** (beads) for issue tracking. Run `bd onboard` to get started.

## What This Project Is

**freshrss-cowork** — a Claude Cowork plugin for FreshRSS. It bundles an MCP server (wrapping the FreshRSS Google Reader API, exposing 10 tools for RSS feed management) plus four skills (`freshrss-digest`, `freshrss-search`, `freshrss-people`, `freshrss-subscriptions`) that drive it.

**Transport**: stdio. Cowork/Claude Code spawn the server as a subprocess via `.mcp.json`, passing `FRESHRSS_URL`/`FRESHRSS_USERNAME`/`FRESHRSS_PASSWORD` from the plugin's `userConfig` (declared in `.claude-plugin/plugin.json`).

**Runtime**: Python 3.12+, managed by `uv`.

## Project Layout

```
freshrss-mcp/
  .claude-plugin/plugin.json  # Plugin manifest + userConfig (url, username, password)
  .mcp.json                   # Bundled MCP server definition (stdio, uv run freshrss-mcp)
  pyproject.toml              # uv/PEP 621 — entry point: freshrss-mcp
  uv.lock                     # Committed lockfile
  .python-version             # 3.13
  skills/
    freshrss-digest/          # /freshrss-digest [timeframe]
    freshrss-search/          # /freshrss-search <topic>
    freshrss-people/          # /freshrss-people [timeframe]
    freshrss-subscriptions/   # /freshrss-subscriptions [timeframe]
  src/freshrss_mcp/
    server.py             # FastMCP entry point (stdio transport)
    tools.py              # 10 MCP tool definitions with error boundaries
    client.py             # FreshRSS Google Reader API client (async, httpx)
    config.py             # pydantic-settings config from env vars
    models.py             # Article and Feed dataclasses
  tests/                  # unit tests
    test_config.py        # Config validation, defaults, secret masking
    test_client.py        # Auth, feeds, articles, ID extraction, edge cases
    test_tools.py         # Every tool happy path + error boundary
    test_models.py        # Serialization, construction, mutability
```

## Key Architecture Decisions

1. **Lazy authentication**: `client.py` calls `_ensure_authenticated()` before every API method. No need to pre-auth at startup.

2. **Error boundaries**: Every tool in `tools.py` catches all exceptions and returns `"Error: ..."` strings. MCP protocol never sees uncaught exceptions.

3. **pydantic-settings**: `config.py` uses `BaseSettings` with `SecretStr` for the password. Missing env vars produce clear validation errors at startup.

4. **Single client instance**: `FreshRSSClient` is created once in `server.py` and shared across all tool calls. No per-call client creation.

5. **No version pins**: `pyproject.toml` has no version constraints on dependencies, per the MCP build spec.

6. **stdio only**: the server is launched by Cowork/Claude Code as a plugin-bundled subprocess (see `.mcp.json`). It is not designed to run standalone as a network service.

## How to Run

```bash
# Dev
uv sync && uv run pytest -v

# Run the server directly for debugging (stdio — needs an MCP client on the other end,
# e.g. `npx @modelcontextprotocol/inspector uv run freshrss-mcp`)
export FRESHRSS_URL="https://freshrss.example.com"
export FRESHRSS_USERNAME="youruser"
export FRESHRSS_PASSWORD="..."
uv run freshrss-mcp
```

## Quick Reference

```bash
bd ready          # Find available work
bd show <id>      # View issue details
bd update <id> --status in_progress  # Claim work
bd close <id>     # Complete work
bd sync           # Sync with git
```

## Landing the Plane (Session Completion)

When ending a session, you MUST:

1. File issues for remaining work
2. Run quality gates: `uv run pytest -v` and `ruff check src/ tests/`
3. Update issue status via `bd close`
4. Push to remote:
   ```bash
   git pull --rebase && bd sync && git push
   git status  # MUST show "up to date with origin"
   ```

Work is NOT complete until `git push` succeeds.
