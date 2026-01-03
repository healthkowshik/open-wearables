"""MCP tools for querying time-series data."""

import contextlib
from datetime import datetime
from typing import Callable
from uuid import UUID

from fastmcp import FastMCP

from app.schemas import TimeSeriesQueryParams
from app.schemas.series_types import SeriesType
from app.services.timeseries_service import timeseries_service


def register_timeseries_tools(mcp: FastMCP, get_db_session: Callable) -> None:
    """Register time-series data MCP tools."""

    @mcp.tool
    def get_timeseries(
        user_id: str,
        series_types: list[str],
        start_datetime: str,
        end_datetime: str,
        limit: int = 100,
    ) -> dict:
        """Get time-series health data for a user.

        Args:
            user_id: The UUID of the user
            series_types: List of series types to retrieve (e.g., ['heart_rate', 'steps'])
                         Use the health://series-types resource to see all available types.
            start_datetime: Start datetime in ISO 8601 format (e.g., '2024-01-01T00:00:00Z')
            end_datetime: End datetime in ISO 8601 format
            limit: Maximum number of data points to return (default 100, max 1000)

        Returns:
            Dictionary with time-series data points and metadata.
            Each data point includes timestamp, type, value, and unit.
        """
        import asyncio

        # Parse datetimes
        start_dt = datetime.fromisoformat(start_datetime.replace("Z", "+00:00"))
        end_dt = datetime.fromisoformat(end_datetime.replace("Z", "+00:00"))

        # Convert string types to SeriesType enum
        types = []
        for st in series_types:
            with contextlib.suppress(ValueError):
                types.append(SeriesType(st))

        if not types:
            return {
                "error": "No valid series types provided. "
                "Valid types include: heart_rate, steps, resting_heart_rate, etc.",
                "data": [],
            }

        with get_db_session() as db:
            params = TimeSeriesQueryParams(
                start_datetime=start_dt,
                end_datetime=end_dt,
                limit=min(limit, 1000),
            )

            # Run async service method
            result = asyncio.get_event_loop().run_until_complete(
                timeseries_service.get_timeseries(db, UUID(user_id), types, params)
            )

            return {
                "data": [
                    {
                        "timestamp": sample.timestamp.isoformat() if sample.timestamp else None,
                        "type": sample.type.value if sample.type else None,
                        "value": sample.value,
                        "unit": sample.unit,
                    }
                    for sample in result.data
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
                    "requested_types": series_types,
                },
            }

    @mcp.tool
    def get_heart_rate_data(
        user_id: str,
        start_datetime: str,
        end_datetime: str,
        include_resting: bool = True,
        limit: int = 100,
    ) -> dict:
        """Get heart rate data for a user.

        A convenience tool specifically for heart rate data.

        Args:
            user_id: The UUID of the user
            start_datetime: Start datetime in ISO 8601 format
            end_datetime: End datetime in ISO 8601 format
            include_resting: Also include resting heart rate data (default True)
            limit: Maximum number of data points (default 100, max 1000)

        Returns:
            Dictionary with heart rate data points.
        """
        import asyncio

        # Parse datetimes
        start_dt = datetime.fromisoformat(start_datetime.replace("Z", "+00:00"))
        end_dt = datetime.fromisoformat(end_datetime.replace("Z", "+00:00"))

        types = [SeriesType.heart_rate]
        if include_resting:
            types.append(SeriesType.resting_heart_rate)

        with get_db_session() as db:
            params = TimeSeriesQueryParams(
                start_datetime=start_dt,
                end_datetime=end_dt,
                limit=min(limit, 1000),
            )

            result = asyncio.get_event_loop().run_until_complete(
                timeseries_service.get_timeseries(db, UUID(user_id), types, params)
            )

            return {
                "heart_rate_data": [
                    {
                        "timestamp": sample.timestamp.isoformat() if sample.timestamp else None,
                        "type": sample.type.value if sample.type else None,
                        "value_bpm": sample.value,
                    }
                    for sample in result.data
                ],
                "sample_count": len(result.data),
                "has_more": result.pagination.has_more,
            }

    @mcp.tool
    def get_steps_data(
        user_id: str,
        start_datetime: str,
        end_datetime: str,
        limit: int = 100,
    ) -> dict:
        """Get step count data for a user.

        A convenience tool specifically for step data.

        Args:
            user_id: The UUID of the user
            start_datetime: Start datetime in ISO 8601 format
            end_datetime: End datetime in ISO 8601 format
            limit: Maximum number of data points (default 100, max 1000)

        Returns:
            Dictionary with step count data points.
        """
        import asyncio

        # Parse datetimes
        start_dt = datetime.fromisoformat(start_datetime.replace("Z", "+00:00"))
        end_dt = datetime.fromisoformat(end_datetime.replace("Z", "+00:00"))

        with get_db_session() as db:
            params = TimeSeriesQueryParams(
                start_datetime=start_dt,
                end_datetime=end_dt,
                limit=min(limit, 1000),
            )

            result = asyncio.get_event_loop().run_until_complete(
                timeseries_service.get_timeseries(db, UUID(user_id), [SeriesType.steps], params)
            )

            return {
                "steps_data": [
                    {
                        "timestamp": sample.timestamp.isoformat() if sample.timestamp else None,
                        "steps": int(sample.value) if sample.value else 0,
                    }
                    for sample in result.data
                ],
                "sample_count": len(result.data),
                "has_more": result.pagination.has_more,
            }
