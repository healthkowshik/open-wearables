"""Shared formatting utilities for MCP tools."""

from datetime import datetime


def format_duration_minutes(minutes: int | None) -> str | None:
    """Format duration in minutes to human-readable string.

    Args:
        minutes: Duration in minutes

    Returns:
        Formatted string like "7h 45m" or None if input is None
    """
    if minutes is None:
        return None
    hours = minutes // 60
    mins = minutes % 60
    if hours > 0:
        return f"{hours}h {mins}m"
    return f"{mins}m"


def format_duration_seconds(seconds: int | None) -> str | None:
    """Format duration in seconds to human-readable string.

    Args:
        seconds: Duration in seconds

    Returns:
        Formatted string like "1h 23m" or "45m" or None if input is None
    """
    if seconds is None:
        return None
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    if hours > 0:
        return f"{hours}h {minutes}m"
    return f"{minutes}m"


def format_distance_km(meters: float | None) -> str | None:
    """Format distance in meters to kilometers with unit.

    Args:
        meters: Distance in meters

    Returns:
        Formatted string like "7.50 km" or "12.3 km" or None if input is None
    """
    if meters is None:
        return None
    km = meters / 1000
    if km >= 10:
        return f"{km:.1f} km"
    return f"{km:.2f} km"


def format_pace(sec_per_km: int | None) -> str | None:
    """Format pace in seconds per km to 'X:XX min/km' format.

    Args:
        sec_per_km: Pace in seconds per kilometer

    Returns:
        Formatted string like "6:16 min/km" or None if input is None
    """
    if sec_per_km is None:
        return None
    minutes = sec_per_km // 60
    seconds = sec_per_km % 60
    return f"{minutes}:{seconds:02d} min/km"


def parse_datetime(dt_str: str | None) -> tuple[str | None, str | None]:
    """Parse ISO datetime string into date and time components.

    Args:
        dt_str: ISO format datetime string (e.g., "2025-01-14T07:15:00Z")

    Returns:
        Tuple of (date_str, time_str) in formats "YYYY-MM-DD" and "HH:MM"
        Returns (None, None) if input is None or invalid
    """
    if not dt_str:
        return None, None
    try:
        dt = datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
        return dt.strftime("%Y-%m-%d"), dt.strftime("%H:%M")
    except (ValueError, AttributeError):
        return None, None


def parse_time(dt_str: str | None) -> str | None:
    """Extract time portion from ISO datetime string.

    Args:
        dt_str: ISO format datetime string

    Returns:
        Time string in "HH:MM" format or None if input is None/invalid
    """
    _, time_str = parse_datetime(dt_str)
    return time_str
