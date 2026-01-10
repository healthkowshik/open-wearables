"""Open Wearables MCP Server.

A Model Context Protocol server that enables LLM clients to query
health and wearable data from the Open Wearables platform.

Usage:
    python -m open_wearables_mcp
"""

from contextlib import contextmanager
from typing import Iterator

from fastmcp import FastMCP

from app.database import SessionLocal
from open_wearables_mcp.tools.users import register_user_tools

# Initialize FastMCP server
mcp = FastMCP(
    name="Open Wearables MCP",
    instructions="""
    Open Wearables MCP Server provides access to health and wearable data.

    To query data, you need a user_id. Use list_users to find available users,
    then use get_user to get details about a specific user.
    """,
)


@contextmanager
def get_db_session() -> Iterator:
    """Context manager for database sessions."""
    db = SessionLocal()
    try:
        yield db
    except Exception as exc:
        db.rollback()
        raise exc
    finally:
        db.close()


# Register user tools
register_user_tools(mcp, get_db_session)


if __name__ == "__main__":
    mcp.run()  # stdio transport (default) - spawned by MCP clients
