"""Entry point for running the MCP server as a module.

Usage:
    python -m mcp
"""

from mcp.server import mcp

if __name__ == "__main__":
    mcp.run()
