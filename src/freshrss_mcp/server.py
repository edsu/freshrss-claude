"""MCP Server entry point for FreshRSS.

Runs FastMCP over stdio, the transport Claude Cowork/Claude Code use to
launch plugin-bundled MCP servers as a subprocess.
"""

import asyncio
import logging
import signal
import sys

from fastmcp import FastMCP

from .client import FreshRSSClient
from .config import load_config
from .tools import register_tools

logging.basicConfig(
    stream=sys.stderr,
    level=logging.INFO,
    format="%(asctime)s %(name)s %(levelname)s %(message)s",
)
logger = logging.getLogger(__name__)


def main() -> None:
    """Run the FreshRSS MCP server."""
    config = load_config()
    client = FreshRSSClient(config)

    mcp = FastMCP("freshrss-mcp")
    register_tools(mcp, client)

    def handle_shutdown(signum: int, frame: object) -> None:
        logger.info("Received shutdown signal, closing connections...")
        asyncio.run(client.aclose())
        sys.exit(0)

    signal.signal(signal.SIGTERM, handle_shutdown)
    signal.signal(signal.SIGINT, handle_shutdown)

    logger.info("Starting FreshRSS MCP server (stdio)")
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
