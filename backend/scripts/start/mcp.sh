#!/bin/bash
# Start the Open Wearables MCP Server
#
# Usage:
#   ./scripts/start/mcp.sh
#
# The MCP server uses STDIO transport by default, suitable for use with
# Claude Desktop and other MCP clients.
#
# Environment variables:
#   - All database and config variables from the main app are supported
#   - See config/.env for available settings

set -e

cd "$(dirname "$0")/../.."

echo "Starting Open Wearables MCP Server..."
uv run python -m mcp_server
