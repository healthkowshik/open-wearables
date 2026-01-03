"""MCP tools for health data analytics and summaries."""

from datetime import datetime
from typing import Callable
from uuid import UUID

from fastmcp import FastMCP

from app.schemas import EventRecordQueryParams, TimeSeriesQueryParams
from app.schemas.series_types import SeriesType
from app.services.event_record_service import event_record_service
from app.services.timeseries_service import timeseries_service


def register_analytics_tools(mcp: FastMCP, get_db_session: Callable) -> None:
    """Register analytics and summary MCP tools."""

    @mcp.tool
    def get_workout_summary(
        user_id: str,
        start_date: str,
        end_date: str,
    ) -> dict:
        """Get aggregated workout statistics for a user over a date range.

        Args:
            user_id: The UUID of the user
            start_date: Start date in ISO 8601 format (e.g., '2024-01-01')
            end_date: End date in ISO 8601 format

        Returns:
            Summary statistics including total workouts, duration, and breakdown by type.
        """
        import asyncio

        start_datetime = datetime.fromisoformat(start_date.replace("Z", "+00:00"))
        end_datetime = datetime.fromisoformat(end_date.replace("Z", "+00:00"))

        with get_db_session() as db:
            # Get all workouts in the range (up to 500 for summary)
            params = EventRecordQueryParams(
                start_datetime=start_datetime,
                end_datetime=end_datetime,
                limit=500,
            )

            result = asyncio.get_event_loop().run_until_complete(
                event_record_service.get_workouts(db, UUID(user_id), params)
            )

            workouts = result.data

            if not workouts:
                return {
                    "total_workouts": 0,
                    "total_duration_seconds": 0,
                    "total_duration_hours": 0,
                    "workout_types": {},
                    "avg_duration_minutes": 0,
                    "period": {"start": start_date, "end": end_date},
                }

            # Aggregate statistics
            total_duration = sum(w.duration_seconds or 0 for w in workouts)
            type_counts: dict[str, int] = {}
            type_durations: dict[str, int] = {}
            hr_values: list[int] = []

            for w in workouts:
                wtype = w.type or "unknown"
                type_counts[wtype] = type_counts.get(wtype, 0) + 1
                type_durations[wtype] = type_durations.get(wtype, 0) + (w.duration_seconds or 0)
                if w.avg_heart_rate_bpm:
                    hr_values.append(w.avg_heart_rate_bpm)

            return {
                "total_workouts": len(workouts),
                "total_duration_seconds": total_duration,
                "total_duration_hours": round(total_duration / 3600, 2),
                "avg_duration_minutes": round(total_duration / len(workouts) / 60, 1) if workouts else 0,
                "workout_types": {
                    wtype: {
                        "count": count,
                        "total_duration_minutes": round(type_durations.get(wtype, 0) / 60, 1),
                    }
                    for wtype, count in sorted(type_counts.items(), key=lambda x: x[1], reverse=True)
                },
                "heart_rate": {
                    "avg_across_workouts": round(sum(hr_values) / len(hr_values), 1) if hr_values else None,
                    "workouts_with_hr_data": len(hr_values),
                }
                if hr_values
                else None,
                "period": {"start": start_date, "end": end_date},
            }

    @mcp.tool
    def get_sleep_summary(
        user_id: str,
        start_date: str,
        end_date: str,
    ) -> dict:
        """Get aggregated sleep statistics for a user over a date range.

        Args:
            user_id: The UUID of the user
            start_date: Start date in ISO 8601 format (e.g., '2024-01-01')
            end_date: End date in ISO 8601 format

        Returns:
            Summary statistics including average duration, efficiency, and sleep stage breakdown.
        """
        import asyncio

        start_datetime = datetime.fromisoformat(start_date.replace("Z", "+00:00"))
        end_datetime = datetime.fromisoformat(end_date.replace("Z", "+00:00"))

        with get_db_session() as db:
            params = EventRecordQueryParams(
                start_datetime=start_datetime,
                end_datetime=end_datetime,
                limit=100,
            )

            result = asyncio.get_event_loop().run_until_complete(
                event_record_service.get_sleep_sessions(db, UUID(user_id), params)
            )

            sessions = result.data

            # Filter out naps for main sleep analysis
            main_sleeps = [s for s in sessions if not s.is_nap]
            naps = [s for s in sessions if s.is_nap]

            if not sessions:
                return {
                    "total_sessions": 0,
                    "main_sleep_sessions": 0,
                    "naps": 0,
                    "period": {"start": start_date, "end": end_date},
                }

            # Calculate averages for main sleep
            total_duration = sum(s.duration_seconds or 0 for s in main_sleeps)
            efficiencies = [s.efficiency_percent for s in main_sleeps if s.efficiency_percent is not None]

            # Aggregate sleep stages
            stage_totals = {"deep": 0, "light": 0, "rem": 0, "awake": 0}
            sessions_with_stages = 0
            for s in main_sleeps:
                if s.stages:
                    sessions_with_stages += 1
                    stage_totals["deep"] += s.stages.deep_seconds or 0
                    stage_totals["light"] += s.stages.light_seconds or 0
                    stage_totals["rem"] += s.stages.rem_seconds or 0
                    stage_totals["awake"] += s.stages.awake_seconds or 0

            avg_duration = total_duration / len(main_sleeps) if main_sleeps else 0

            return {
                "total_sessions": len(sessions),
                "main_sleep_sessions": len(main_sleeps),
                "naps": len(naps),
                "avg_duration_hours": round(avg_duration / 3600, 2) if main_sleeps else 0,
                "avg_duration_minutes": round(avg_duration / 60, 1) if main_sleeps else 0,
                "total_sleep_hours": round(total_duration / 3600, 2),
                "avg_efficiency_percent": round(sum(efficiencies) / len(efficiencies), 1) if efficiencies else None,
                "sleep_stages_avg": {
                    "deep_minutes": round(stage_totals["deep"] / sessions_with_stages / 60, 1)
                    if sessions_with_stages
                    else None,
                    "light_minutes": round(stage_totals["light"] / sessions_with_stages / 60, 1)
                    if sessions_with_stages
                    else None,
                    "rem_minutes": round(stage_totals["rem"] / sessions_with_stages / 60, 1)
                    if sessions_with_stages
                    else None,
                    "awake_minutes": round(stage_totals["awake"] / sessions_with_stages / 60, 1)
                    if sessions_with_stages
                    else None,
                    "deep_percent": round(
                        stage_totals["deep"]
                        / (stage_totals["deep"] + stage_totals["light"] + stage_totals["rem"])
                        * 100,
                        1,
                    )
                    if (stage_totals["deep"] + stage_totals["light"] + stage_totals["rem"]) > 0
                    else None,
                    "rem_percent": round(
                        stage_totals["rem"]
                        / (stage_totals["deep"] + stage_totals["light"] + stage_totals["rem"])
                        * 100,
                        1,
                    )
                    if (stage_totals["deep"] + stage_totals["light"] + stage_totals["rem"]) > 0
                    else None,
                }
                if sessions_with_stages
                else None,
                "period": {"start": start_date, "end": end_date},
            }

    @mcp.tool
    def get_heart_rate_stats(
        user_id: str,
        start_date: str,
        end_date: str,
    ) -> dict:
        """Get heart rate statistics for a user over a date range.

        Args:
            user_id: The UUID of the user
            start_date: Start date in ISO 8601 format (e.g., '2024-01-01')
            end_date: End date in ISO 8601 format

        Returns:
            Heart rate statistics including min, max, average, and resting HR data.
        """
        import asyncio

        start_datetime = datetime.fromisoformat(start_date.replace("Z", "+00:00"))
        end_datetime = datetime.fromisoformat(end_date.replace("Z", "+00:00"))

        with get_db_session() as db:
            # Get heart rate data
            params = TimeSeriesQueryParams(
                start_datetime=start_datetime,
                end_datetime=end_datetime,
                limit=10000,  # Get more data for accurate stats
            )

            types = [SeriesType.heart_rate, SeriesType.resting_heart_rate]
            result = asyncio.get_event_loop().run_until_complete(
                timeseries_service.get_timeseries(db, UUID(user_id), types, params)
            )

            hr_values = []
            resting_hr_values = []

            for sample in result.data:
                if sample.type == SeriesType.heart_rate:
                    hr_values.append(sample.value)
                elif sample.type == SeriesType.resting_heart_rate:
                    resting_hr_values.append(sample.value)

            if not hr_values and not resting_hr_values:
                return {
                    "heart_rate": None,
                    "resting_heart_rate": None,
                    "data_points": 0,
                    "period": {"start": start_date, "end": end_date},
                }

            return {
                "heart_rate": {
                    "min_bpm": round(min(hr_values), 1) if hr_values else None,
                    "max_bpm": round(max(hr_values), 1) if hr_values else None,
                    "avg_bpm": round(sum(hr_values) / len(hr_values), 1) if hr_values else None,
                    "data_points": len(hr_values),
                }
                if hr_values
                else None,
                "resting_heart_rate": {
                    "min_bpm": round(min(resting_hr_values), 1) if resting_hr_values else None,
                    "max_bpm": round(max(resting_hr_values), 1) if resting_hr_values else None,
                    "avg_bpm": round(sum(resting_hr_values) / len(resting_hr_values), 1) if resting_hr_values else None,
                    "data_points": len(resting_hr_values),
                }
                if resting_hr_values
                else None,
                "total_data_points": len(hr_values) + len(resting_hr_values),
                "period": {"start": start_date, "end": end_date},
            }

    @mcp.tool
    def get_activity_summary(
        user_id: str,
        start_date: str,
        end_date: str,
    ) -> dict:
        """Get activity summary including steps, energy, and exercise time.

        Args:
            user_id: The UUID of the user
            start_date: Start date in ISO 8601 format (e.g., '2024-01-01')
            end_date: End date in ISO 8601 format

        Returns:
            Activity summary with total steps, calories, and exercise time.
        """
        import asyncio

        start_datetime = datetime.fromisoformat(start_date.replace("Z", "+00:00"))
        end_datetime = datetime.fromisoformat(end_date.replace("Z", "+00:00"))

        with get_db_session() as db:
            params = TimeSeriesQueryParams(
                start_datetime=start_datetime,
                end_datetime=end_datetime,
                limit=10000,
            )

            types = [SeriesType.steps, SeriesType.energy, SeriesType.exercise_time]
            result = asyncio.get_event_loop().run_until_complete(
                timeseries_service.get_timeseries(db, UUID(user_id), types, params)
            )

            steps_values = []
            energy_values = []
            exercise_values = []

            for sample in result.data:
                if sample.type == SeriesType.steps:
                    steps_values.append(sample.value)
                elif sample.type == SeriesType.energy:
                    energy_values.append(sample.value)
                elif sample.type == SeriesType.exercise_time:
                    exercise_values.append(sample.value)

            return {
                "steps": {
                    "total": int(sum(steps_values)) if steps_values else 0,
                    "avg_per_day": int(
                        sum(steps_values)
                        / max(
                            1,
                            len(
                                set(
                                    s.timestamp.date()
                                    for s in result.data
                                    if s.type == SeriesType.steps and s.timestamp
                                )
                            ),
                        )
                    )
                    if steps_values
                    else 0,
                    "data_points": len(steps_values),
                }
                if steps_values
                else None,
                "energy": {
                    "total_kcal": round(sum(energy_values), 1) if energy_values else 0,
                    "avg_kcal_per_day": round(
                        sum(energy_values)
                        / max(
                            1,
                            len(
                                set(
                                    s.timestamp.date()
                                    for s in result.data
                                    if s.type == SeriesType.energy and s.timestamp
                                )
                            ),
                        ),
                        1,
                    )
                    if energy_values
                    else 0,
                    "data_points": len(energy_values),
                }
                if energy_values
                else None,
                "exercise_time": {
                    "total_minutes": round(sum(exercise_values), 1) if exercise_values else 0,
                    "data_points": len(exercise_values),
                }
                if exercise_values
                else None,
                "period": {"start": start_date, "end": end_date},
            }
