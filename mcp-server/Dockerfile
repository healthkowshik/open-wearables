# Open Wearables MCP Server Dockerfile
#
# Build context should be the repository root:
#   docker build -f mcp-server/Dockerfile -t open-wearables-mcp:latest .
#
# Run:
#   docker run -i --rm --init \
#     --network open-wearables_default \
#     -e DB_HOST=db \
#     open-wearables-mcp:latest

FROM python:3.13-slim AS builder

RUN apt-get update && \
    apt-get install -y --no-install-recommends build-essential libpq-dev && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

# Copy backend dependencies and code (needed for app.* imports)
COPY backend/pyproject.toml backend/uv.lock /app/backend/
COPY backend/app /app/backend/app

# Copy MCP server
COPY mcp-server/pyproject.toml /app/mcp-server/
COPY mcp-server/src /app/mcp-server/src

# Install backend dependencies (for app.* imports)
WORKDIR /app/backend
ENV VIRTUAL_ENV=/opt/venv
RUN uv venv $VIRTUAL_ENV
ENV PATH="$VIRTUAL_ENV/bin:$PATH"
RUN uv sync --locked --no-dev

# Install MCP server dependencies
WORKDIR /app/mcp-server
RUN uv sync --no-dev

FROM python:3.13-slim

RUN apt-get update && \
    apt-get install -y --no-install-recommends libpq5 && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

COPY --from=builder /opt/venv /opt/venv
COPY --from=builder /app /app

ENV VIRTUAL_ENV=/opt/venv
ENV PATH="/opt/venv/bin:$PATH"
ENV UV_PROJECT_ENVIRONMENT=/opt/venv
ENV PYTHONPATH="/app/backend"

WORKDIR /app/mcp-server

# Entry point - stdio transport for MCP
CMD ["uv", "run", "python", "-m", "open_wearables_mcp"]
