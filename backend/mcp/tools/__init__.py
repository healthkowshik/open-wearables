"""MCP tools for querying health and wearable data."""

from mcp.tools.analytics import register_analytics_tools
from mcp.tools.sleep import register_sleep_tools
from mcp.tools.timeseries import register_timeseries_tools
from mcp.tools.users import register_user_tools
from mcp.tools.workouts import register_workout_tools

__all__ = [
    "register_user_tools",
    "register_workout_tools",
    "register_sleep_tools",
    "register_timeseries_tools",
    "register_analytics_tools",
]
