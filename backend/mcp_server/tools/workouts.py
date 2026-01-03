"""MCP tools for querying workout data."""

from datetime import datetime
from typing import Callable
from uuid import UUID

from fastmcp import FastMCP

from app.schemas import EventRecordQueryParams
from app.services.event_record_service import event_record_service


def register_workout_tools(mcp: FastMCP, get_db_session: Callable) -> None:
    """Register workout-related MCP tools."""

    @mcp.tool
    def get_workouts(
        user_id: str,
        start_date: str | None = None,
        end_date: str | None = None,
        workout_type: str | None = None,
        limit: int = 20,
    ) -> dict:
        """Get workouts for a user within a date range.

        Args:
            user_id: The UUID of the user
            start_date: Start date in ISO 8601 format (e.g., '2024-01-01' or '2024-01-01T00:00:00Z')
            end_date: End date in ISO 8601 format
            workout_type: Optional filter by workout type (e.g., 'running', 'cycling', 'swimming')
            limit: Maximum number of results (default 20, max 100)

        Returns:
            Dictionary with workouts list and pagination info.
            Each workout includes type, duration, heart rate stats, and distance.
        """
        import asyncio

        # Parse dates
        start_datetime = None
        end_datetime = None
        if start_date:
            start_datetime = datetime.fromisoformat(start_date.replace("Z", "+00:00"))
        if end_date:
            end_datetime = datetime.fromisoformat(end_date.replace("Z", "+00:00"))

        with get_db_session() as db:
            params = EventRecordQueryParams(
                start_datetime=start_datetime,
                end_datetime=end_datetime,
                type=workout_type,
                limit=min(limit, 100),
            )

            # Run async service method
            result = asyncio.get_event_loop().run_until_complete(
                event_record_service.get_workouts(db, UUID(user_id), params)
            )

            return {
                "workouts": [
                    {
                        "id": str(workout.id),
                        "type": workout.type,
                        "name": workout.name,
                        "start_time": workout.start_time.isoformat() if workout.start_time else None,
                        "end_time": workout.end_time.isoformat() if workout.end_time else None,
                        "duration_seconds": workout.duration_seconds,
                        "duration_minutes": round(workout.duration_seconds / 60, 1)
                        if workout.duration_seconds
                        else None,
                        "source": {
                            "provider": workout.source.provider if workout.source else None,
                            "device": workout.source.device if workout.source else None,
                        },
                        "calories_kcal": workout.calories_kcal,
                        "distance_meters": workout.distance_meters,
                        "distance_km": round(workout.distance_meters / 1000, 2) if workout.distance_meters else None,
                        "avg_heart_rate_bpm": workout.avg_heart_rate_bpm,
                        "max_heart_rate_bpm": workout.max_heart_rate_bpm,
                        "elevation_gain_meters": workout.elevation_gain_meters,
                    }
                    for workout in result.data
                ],
                "pagination": {
                    "has_more": result.pagination.has_more,
                    "total_count": result.pagination.total_count,
                },
                "metadata": {
                    "sample_count": result.metadata.sample_count if result.metadata else len(result.data),
                    "start_time": result.metadata.start_time.isoformat()
                    if result.metadata and result.metadata.start_time
                    else None,
                    "end_time": result.metadata.end_time.isoformat()
                    if result.metadata and result.metadata.end_time
                    else None,
                },
            }
