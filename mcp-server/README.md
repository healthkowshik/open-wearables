# Open Wearables MCP Server

A [Model Context Protocol (MCP)](https://modelcontextprotocol.io/) server that enables LLM clients to query health and wearable data from the Open Wearables platform.

## Overview

This MCP server allows AI assistants like Claude to interact with the Open Wearables database through natural language. It exposes tools for querying users, health metrics, and wearable data.

## Transport

The MCP server uses **stdio transport**, which means:
- MCP clients spawn the server as a subprocess
- Communication happens via stdin/stdout
- A new server instance is created per session

This is the recommended approach per the [MCP specification](https://modelcontextprotocol.io/specification/2025-06-18/basic/transports).

## Available Tools

| Tool | Description |
|------|-------------|
| `list_users` | List users with pagination and search |
| `get_user` | Get detailed information for a specific user |

## Configuration

### Prerequisites

- Docker Desktop running
- The `open-wearables-platform:latest` image built (`docker compose build`)
- Database container running (`docker compose up db -d`)

### Claude Desktop

Add to `~/Library/Application Support/Claude/claude_desktop_config.json` (macOS) or `%APPDATA%\Claude\claude_desktop_config.json` (Windows):

```json
{
  "mcpServers": {
    "open-wearables": {
      "command": "docker",
      "args": [
        "run",
        "-i",
        "--rm",
        "--init",
        "--network", "open-wearables_default",
        "-e", "DB_HOST=db",
        "open-wearables-platform:latest",
        "mcp-server/scripts/start.sh"
      ]
    }
  }
}
```

### Cursor / VS Code

Add to your MCP configuration:

```json
{
  "mcpServers": {
    "open-wearables": {
      "command": "docker",
      "args": [
        "run", "-i", "--rm", "--init",
        "--network", "open-wearables_default",
        "-e", "DB_HOST=db",
        "open-wearables-platform:latest",
        "mcp-server/scripts/start.sh"
      ]
    }
  }
}
```

## Local Development

### Running locally (without Docker)

```bash
cd mcp-server

# Install dependencies
uv sync

# Set PYTHONPATH to include backend
export PYTHONPATH="../backend:$PYTHONPATH"

# Run the server
uv run python -m open_wearables_mcp
```

### Using MCP Inspector

Test the server with [MCP Inspector](https://github.com/modelcontextprotocol/inspector):

```bash
cd mcp-server
PYTHONPATH="../backend" npx @anthropic-ai/mcp-inspector uv run python -m open_wearables_mcp
```

### Manual Testing

Run the server and paste JSON-RPC messages:

```bash
./scripts/start.sh
```

Initialize:
```json
{"jsonrpc": "2.0", "method": "initialize", "id": 1, "params": {"protocolVersion": "2024-11-05", "capabilities": {}, "clientInfo": {"name": "test", "version": "1.0"}}}
```

List users:
```json
{"jsonrpc": "2.0", "method": "tools/call", "id": 2, "params": {"name": "list_users", "arguments": {}}}
```

## Architecture

The MCP server is a standalone component that imports from the backend `app` module for database access and business logic. This allows it to:

- Reuse existing database models and services
- Stay in sync with backend schema changes
- Maintain consistent business logic

```
open-wearables/
├── backend/           # Main API server
│   └── app/           # Application code (imported by MCP server)
├── frontend/          # Web UI
└── mcp-server/        # This directory
    ├── src/
    │   └── open_wearables_mcp/
    │       ├── server.py    # MCP server setup
    │       └── tools/       # MCP tool definitions
    └── scripts/
        └── start.sh         # Entry point
```
