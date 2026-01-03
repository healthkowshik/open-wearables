"""MCP tools for querying sleep data."""

from datetime import datetime
from typing import Callable
from uuid import UUID

from fastmcp import FastMCP

from app.schemas import EventRecordQueryParams
from app.services.event_record_service import event_record_service


def register_sleep_tools(mcp: FastMCP, get_db_session: Callable) -> None:
    """Register sleep-related MCP tools."""

    @mcp.tool
    def get_sleep_sessions(
        user_id: str,
        start_date: str | None = None,
        end_date: str | None = None,
        limit: int = 20,
    ) -> dict:
        """Get sleep sessions for a user within a date range.

        Args:
            user_id: The UUID of the user
            start_date: Start date in ISO 8601 format (e.g., '2024-01-01')
            end_date: End date in ISO 8601 format
            limit: Maximum number of results (default 20, max 100)

        Returns:
            Dictionary with sleep sessions list and pagination info.
            Each session includes duration, efficiency, and sleep stage breakdown.
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
                limit=min(limit, 100),
            )

            # Run async service method
            result = asyncio.get_event_loop().run_until_complete(
                event_record_service.get_sleep_sessions(db, UUID(user_id), params)
            )

            return {
                "sleep_sessions": [
                    {
                        "id": str(session.id),
                        "start_time": session.start_time.isoformat() if session.start_time else None,
                        "end_time": session.end_time.isoformat() if session.end_time else None,
                        "duration_seconds": session.duration_seconds,
                        "duration_hours": round(session.duration_seconds / 3600, 2)
                        if session.duration_seconds
                        else None,
                        "efficiency_percent": session.efficiency_percent,
                        "is_nap": session.is_nap,
                        "source": {
                            "provider": session.source.provider if session.source else None,
                            "device": session.source.device if session.source else None,
                        },
                        "stages": {
                            "deep_seconds": session.stages.deep_seconds if session.stages else None,
                            "deep_minutes": round(session.stages.deep_seconds / 60, 1)
                            if session.stages and session.stages.deep_seconds
                            else None,
                            "light_seconds": session.stages.light_seconds if session.stages else None,
                            "light_minutes": round(session.stages.light_seconds / 60, 1)
                            if session.stages and session.stages.light_seconds
                            else None,
                            "rem_seconds": session.stages.rem_seconds if session.stages else None,
                            "rem_minutes": round(session.stages.rem_seconds / 60, 1)
                            if session.stages and session.stages.rem_seconds
                            else None,
                            "awake_seconds": session.stages.awake_seconds if session.stages else None,
                            "awake_minutes": round(session.stages.awake_seconds / 60, 1)
                            if session.stages and session.stages.awake_seconds
                            else None,
                        }
                        if session.stages
                        else None,
                    }
                    for session in result.data
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
