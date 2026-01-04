"""Open Wearables MCP Server.

A Model Context Protocol server that enables LLM clients to query
health and wearable data from the Open Wearables platform.

Usage:
    python -m mcp_server.server
"""

import sys
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

# Add parent directory to path to import app modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from fastmcp import FastMCP

from app.database import SessionLocal
from app.schemas.series_types import SERIES_TYPE_DEFINITIONS, SeriesType
from app.schemas.workout_types import WorkoutType
from mcp_server.tools.analytics import register_analytics_tools
from mcp_server.tools.sleep import register_sleep_tools
from mcp_server.tools.timeseries import register_timeseries_tools
from mcp_server.tools.users import register_user_tools
from mcp_server.tools.workouts import register_workout_tools

# Initialize FastMCP server
mcp = FastMCP(
    name="Open Wearables MCP",
    instructions="""
    Open Wearables MCP Server provides access to health and wearable data.

    Available data types:
    - Workouts: Running, cycling, swimming, strength training, etc.
    - Sleep sessions: Duration, efficiency, sleep stages (deep, light, REM, awake)
    - Time-series data: Heart rate, steps, HRV, blood pressure, weight, and more

    To query data, you need a user_id. Use list_users to find available users.
    All date/time parameters should be in ISO 8601 format.
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


# Register all tools
register_user_tools(mcp, get_db_session)
register_workout_tools(mcp, get_db_session)
register_sleep_tools(mcp, get_db_session)
register_timeseries_tools(mcp, get_db_session)
register_analytics_tools(mcp, get_db_session)


# =============================================================================
# RESOURCES
# =============================================================================


@mcp.resource("health://series-types")
def get_series_types() -> dict:
    """Get all available time-series data types and their units.

    Returns a dictionary of series types with their IDs and units.
    Use these type names when querying timeseries data.
    """
    return {
        "series_types": [
            {"id": type_id, "name": series_type.value, "unit": unit}
            for type_id, series_type, unit in SERIES_TYPE_DEFINITIONS
        ],
        "categories": {
            "biometrics_heart": [
                st.value for st in SeriesType if st.value.startswith(("heart_", "resting_heart", "walking_heart"))
            ],
            "biometrics_blood": [
                st.value for st in SeriesType if st.value.startswith(("oxygen_", "blood_", "respiratory_", "sleeping_"))
            ],
            "biometrics_body": [
                st.value
                for st in SeriesType
                if st.value
                in ("height", "weight", "body_fat_percentage", "body_mass_index", "lean_body_mass", "body_temperature")
            ],
            "activity_basic": [
                st.value
                for st in SeriesType
                if st.value
                in (
                    "steps",
                    "energy",
                    "basal_energy",
                    "stand_time",
                    "exercise_time",
                    "physical_effort",
                    "flights_climbed",
                )
            ],
            "activity_distance": [st.value for st in SeriesType if st.value.startswith("distance_")],
            "activity_running": [st.value for st in SeriesType if st.value.startswith("running_")],
            "activity_walking": [
                st.value for st in SeriesType if st.value.startswith("walking_") or st.value.startswith("stair_")
            ],
        },
    }


@mcp.resource("health://workout-types")
def get_workout_types() -> dict:
    """Get all available workout types.

    Returns a dictionary of workout types organized by category.
    Use these type names when filtering workouts.
    """
    return {
        "workout_types": [wt.value for wt in WorkoutType],
        "categories": {
            "running_walking": [
                WorkoutType.RUNNING.value,
                WorkoutType.TRAIL_RUNNING.value,
                WorkoutType.TREADMILL.value,
                WorkoutType.WALKING.value,
                WorkoutType.HIKING.value,
                WorkoutType.MOUNTAINEERING.value,
            ],
            "cycling": [
                WorkoutType.CYCLING.value,
                WorkoutType.MOUNTAIN_BIKING.value,
                WorkoutType.INDOOR_CYCLING.value,
                WorkoutType.E_BIKING.value,
            ],
            "swimming": [
                WorkoutType.SWIMMING.value,
                WorkoutType.POOL_SWIMMING.value,
                WorkoutType.OPEN_WATER_SWIMMING.value,
            ],
            "strength_gym": [
                WorkoutType.STRENGTH_TRAINING.value,
                WorkoutType.CARDIO_TRAINING.value,
                WorkoutType.FITNESS_EQUIPMENT.value,
                WorkoutType.ELLIPTICAL.value,
                WorkoutType.ROWING_MACHINE.value,
            ],
            "flexibility": [
                WorkoutType.YOGA.value,
                WorkoutType.PILATES.value,
                WorkoutType.STRETCHING.value,
            ],
            "winter_sports": [
                WorkoutType.CROSS_COUNTRY_SKIING.value,
                WorkoutType.ALPINE_SKIING.value,
                WorkoutType.SNOWBOARDING.value,
                WorkoutType.ICE_SKATING.value,
            ],
            "water_sports": [
                WorkoutType.ROWING.value,
                WorkoutType.KAYAKING.value,
                WorkoutType.SURFING.value,
                WorkoutType.SAILING.value,
            ],
            "team_sports": [
                WorkoutType.SOCCER.value,
                WorkoutType.BASKETBALL.value,
                WorkoutType.TENNIS.value,
                WorkoutType.VOLLEYBALL.value,
            ],
        },
    }


if __name__ == "__main__":
    mcp.run(transport="sse", host="0.0.0.0", port=8001)
