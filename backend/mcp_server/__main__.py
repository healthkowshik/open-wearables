"""Entry point for running the MCP server as a module.

Usage:
    python -m mcp_server
"""

from mcp_server.server import mcp

if __name__ == "__main__":
    mcp.run()
