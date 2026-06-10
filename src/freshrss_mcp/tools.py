"""MCP tool definitions for FreshRSS.

Each tool does exactly one thing. All exceptions are caught at the
tool boundary and returned as {"error": "..."} dicts so the MCP protocol
never sees an uncaught exception. Successful results are returned as
native Python lists/dicts; FastMCP serializes them to JSON on the wire.
"""

import logging
from typing import Any

from fastmcp import FastMCP

from .client import FreshRSSClient

logger = logging.getLogger(__name__)


def _truncate_summary(summary: str, max_length: int) -> str:
    """Truncate summary to max_length at a word boundary."""
    if len(summary) <= max_length:
        return summary
    return summary[:max_length].rsplit(" ", 1)[0] + "..."


def register_tools(mcp: FastMCP, client: FreshRSSClient) -> None:
    """Register all FreshRSS tools on the given MCP server instance."""

    @mcp.tool()
    async def get_unread_articles(
        limit: int = 20,
        feed_ids: list[int] | None = None,
        since_timestamp: int | None = None,
        max_summary_length: int = 500,
    ) -> list[dict[str, Any]] | dict[str, str]:
        """Get unread articles from FreshRSS.

        Args:
            limit: Maximum number of articles to return (1-100, default 20).
            feed_ids: Optional list of feed IDs to filter by.
            since_timestamp: Only return articles published after this Unix timestamp.
            max_summary_length: Maximum characters for article summaries (default 500).

        Returns a list of article dicts with id, title, summary, url, published
        timestamp, feed_name, is_read, and is_starred fields, or {"error": ...}.
        """
        try:
            if feed_ids:
                all_articles = []
                for fid in feed_ids:
                    articles = await client.get_articles(
                        feed_id=fid,
                        limit=limit,
                        include_read=False,
                        since_timestamp=since_timestamp,
                    )
                    all_articles.extend(articles)
                all_articles.sort(key=lambda a: a.published, reverse=True)
                articles = all_articles[:limit]
            else:
                articles = await client.get_articles(
                    limit=limit,
                    include_read=False,
                    since_timestamp=since_timestamp,
                )

            result = []
            for article in articles:
                d = article.to_dict()
                d["summary"] = _truncate_summary(d["summary"], max_summary_length)
                result.append(d)

            return result
        except Exception as e:
            logger.error("get_unread_articles failed: %s", e, exc_info=True)
            return {"error": str(e)}

    @mcp.tool()
    async def get_articles_by_feed(
        feed_id: int,
        limit: int = 20,
        include_read: bool = False,
        since_timestamp: int | None = None,
    ) -> list[dict[str, Any]] | dict[str, str]:
        """Get articles from a specific feed.

        Args:
            feed_id: ID of the feed to fetch articles from.
            limit: Maximum number of articles to return (1-100, default 20).
            include_read: Whether to include already-read articles (default False).
            since_timestamp: Only return articles published after this Unix timestamp.

        Returns a list of article dicts, or {"error": ...}.
        """
        try:
            articles = await client.get_articles(
                feed_id=feed_id,
                limit=limit,
                include_read=include_read,
                since_timestamp=since_timestamp,
            )
            return [a.to_dict() for a in articles]
        except Exception as e:
            logger.error("get_articles_by_feed failed: %s", e, exc_info=True)
            return {"error": str(e)}

    @mcp.tool()
    async def search_articles(
        query: str,
        limit: int = 10,
        feed_ids: list[int] | None = None,
        since_timestamp: int | None = None,
    ) -> list[dict[str, Any]] | dict[str, str]:
        """Search articles by keyword in title or summary.

        Performs client-side filtering since FreshRSS API lacks server-side search.

        Args:
            query: Search query string (case-insensitive).
            limit: Maximum number of matching articles to return (default 10).
            feed_ids: Optional list of feed IDs to search within.
            since_timestamp: Only return articles published after this Unix timestamp.

        Returns a list of matching article dicts, or {"error": ...}.
        """
        try:
            fetch_limit = limit * 3
            if feed_ids:
                all_articles = []
                for fid in feed_ids:
                    articles = await client.get_articles(
                        feed_id=fid,
                        limit=fetch_limit,
                        include_read=True,
                        since_timestamp=since_timestamp,
                    )
                    all_articles.extend(articles)
            else:
                all_articles = await client.get_articles(
                    limit=fetch_limit,
                    include_read=True,
                    since_timestamp=since_timestamp,
                )

            query_lower = query.lower()
            matching = [
                a
                for a in all_articles
                if query_lower in a.title.lower() or query_lower in a.summary.lower()
            ]
            return [a.to_dict() for a in matching[:limit]]
        except Exception as e:
            logger.error("search_articles failed: %s", e, exc_info=True)
            return {"error": str(e)}

    @mcp.tool()
    async def list_feeds() -> list[dict[str, Any]] | dict[str, str]:
        """List all subscribed feeds with unread counts.

        Returns a list of feed dicts with id, name, url, unread_count, and categories
        fields, or {"error": ...}.
        """
        try:
            feeds = await client.list_feeds()
            unread_counts = await client.get_unread_counts()
            for feed in feeds:
                feed.unread_count = unread_counts.get(feed.id, 0)
            return [f.to_dict() for f in feeds]
        except Exception as e:
            logger.error("list_feeds failed: %s", e, exc_info=True)
            return {"error": str(e)}

    @mcp.tool()
    async def get_feed_info(feed_id: int) -> dict[str, Any]:
        """Get detailed information about a specific feed.

        Args:
            feed_id: ID of the feed.

        Returns a feed dict, or {"error": ...} if the feed is not found.
        """
        try:
            feeds = await client.list_feeds()
            unread_counts = await client.get_unread_counts()
            for feed in feeds:
                if feed.id == feed_id:
                    feed.unread_count = unread_counts.get(feed.id, 0)
                    return feed.to_dict()
            return {"error": f"Feed {feed_id} not found"}
        except Exception as e:
            logger.error("get_feed_info failed: %s", e, exc_info=True)
            return {"error": str(e)}

    @mcp.tool()
    async def get_feed_stats() -> list[dict[str, Any]] | dict[str, str]:
        """Get statistics for all feeds.

        Returns a list of dicts with feed_id, feed_name, and unread_count fields,
        or {"error": ...}.
        """
        try:
            feeds = await client.list_feeds()
            unread_counts = await client.get_unread_counts()
            return [
                {
                    "feed_id": feed.id,
                    "feed_name": feed.name,
                    "unread_count": unread_counts.get(feed.id, 0),
                }
                for feed in feeds
            ]
        except Exception as e:
            logger.error("get_feed_stats failed: %s", e, exc_info=True)
            return {"error": str(e)}

    @mcp.tool()
    async def mark_as_read(article_ids: list[int]) -> dict[str, Any]:
        """Mark articles as read.

        Args:
            article_ids: List of article IDs to mark as read.

        Returns {"ok": True} on success or {"ok": False, "error": ...}.
        """
        try:
            if not article_ids:
                return {"ok": True}
            await client.mark_as_read(article_ids)
            return {"ok": True}
        except Exception as e:
            logger.error("mark_as_read failed: %s", e, exc_info=True)
            return {"ok": False, "error": str(e)}

    @mcp.tool()
    async def mark_as_unread(article_ids: list[int]) -> dict[str, Any]:
        """Mark articles as unread.

        Args:
            article_ids: List of article IDs to mark as unread.

        Returns {"ok": True} on success or {"ok": False, "error": ...}.
        """
        try:
            if not article_ids:
                return {"ok": True}
            await client.mark_as_unread(article_ids)
            return {"ok": True}
        except Exception as e:
            logger.error("mark_as_unread failed: %s", e, exc_info=True)
            return {"ok": False, "error": str(e)}

    @mcp.tool()
    async def star_article(article_id: int) -> dict[str, Any]:
        """Star/favorite an article.

        Args:
            article_id: ID of the article to star.

        Returns {"ok": True} on success or {"ok": False, "error": ...}.
        """
        try:
            await client.star_article(article_id)
            return {"ok": True}
        except Exception as e:
            logger.error("star_article failed: %s", e, exc_info=True)
            return {"ok": False, "error": str(e)}

    @mcp.tool()
    async def unstar_article(article_id: int) -> dict[str, Any]:
        """Remove star from an article.

        Args:
            article_id: ID of the article to unstar.

        Returns {"ok": True} on success or {"ok": False, "error": ...}.
        """
        try:
            await client.unstar_article(article_id)
            return {"ok": True}
        except Exception as e:
            logger.error("unstar_article failed: %s", e, exc_info=True)
            return {"ok": False, "error": str(e)}
