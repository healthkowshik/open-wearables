#!/bin/bash
# Start the Open Wearables MCP Server
#
# Usage:
#   ./scripts/start.sh
#
# The MCP server uses stdio transport (stdin/stdout).
# It is spawned by MCP clients (e.g., Claude Desktop) as a subprocess.
#
# Environment variables:
#   - All database and config variables from the main app are supported
#   - See backend/config/.env for available settings

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
MCP_SERVER_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
PROJECT_ROOT="$(cd "$MCP_SERVER_DIR/.." && pwd)"

# Add backend to PYTHONPATH so we can import app modules
export PYTHONPATH="${PROJECT_ROOT}/backend:${PYTHONPATH:-}"

cd "$MCP_SERVER_DIR"

# Note: No echo statements here - stdout is reserved for MCP protocol messages
# Any debug output should go to stderr
uv run python -m open_wearables_mcp
