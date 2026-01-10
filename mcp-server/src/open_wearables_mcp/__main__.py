"""Entry point for running the MCP server as a module.

Usage:
    python -m open_wearables_mcp

Note: When running in Docker, use --init flag to ensure proper signal
handling and clean shutdown when the MCP client disconnects.
"""

from open_wearables_mcp import main

if __name__ == "__main__":
    main()
