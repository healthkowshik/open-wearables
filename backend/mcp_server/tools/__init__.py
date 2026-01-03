"""MCP tools for querying health and wearable data."""

from mcp_server.tools.analytics import register_analytics_tools
from mcp_server.tools.sleep import register_sleep_tools
from mcp_server.tools.timeseries import register_timeseries_tools
from mcp_server.tools.users import register_user_tools
from mcp_server.tools.workouts import register_workout_tools

__all__ = [
    "register_user_tools",
    "register_workout_tools",
    "register_sleep_tools",
    "register_timeseries_tools",
    "register_analytics_tools",
]
