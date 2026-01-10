"""Open Wearables MCP Server.

A Model Context Protocol server that enables LLM clients to query
health and wearable data from the Open Wearables platform.
"""

from open_wearables_mcp.server import mcp


def main() -> None:
    """Entry point for the MCP server."""
    mcp.run()


__all__ = ["main", "mcp"]
