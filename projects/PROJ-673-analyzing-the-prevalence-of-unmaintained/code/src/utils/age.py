"""
Age calculation utilities for dependency analysis.

Implements FR-010: Calculate age_in_days while handling missing release metadata.
Dependencies with missing release metadata have age_in_days=null but are still
included in vulnerability counts.
"""

from datetime import datetime, timezone
from typing import Optional, Union
import logging

logger = logging.getLogger(__name__)


def parse_date(date_string: Optional[str]) -> Optional[datetime]:
    """
    Parse an ISO format date string into a datetime object.

    Args:
        date_string: ISO format date string (e.g., "2023-01-15T10:30:00Z")

    Returns:
        datetime object or None if input is None or invalid
    """
    if date_string is None:
        return None

    if not isinstance(date_string, str):
        logger.warning(f"Invalid date type: {type(date_string)}, expected str")
        return None

    date_string = date_string.strip()
    if not date_string:
        return None

    try:
        # Handle various ISO formats
        if date_string.endswith('Z'):
            date_string = date_string[:-1] + '+00:00'

        # Try parsing with timezone
        try:
            dt = datetime.fromisoformat(date_string)
            # Convert to UTC if timezone aware
            if dt.tzinfo is not None:
                dt = dt.astimezone(timezone.utc)
            return dt
        except ValueError:
            # Try without timezone
            dt = datetime.fromisoformat(date_string.replace('Z', ''))
            return dt.replace(tzinfo=timezone.utc)
    except Exception as e:
        logger.warning(f"Failed to parse date '{date_string}': {e}")
        return None


def calculate_age_in_days(last_release_date: Optional[Union[str, datetime]]) -> Optional[float]:
    """
    Calculate the age in days since the last release date.

    Implements FR-010: Returns None for missing release dates, but does not
    affect vulnerability count calculations.

    Args:
        last_release_date: The last release date as an ISO string or datetime object.
                           Can be None/missing.

    Returns:
        float: Age in days since last release, or None if date is missing/invalid.
               Never raises - returns None for missing data to allow inclusion
               in vulnerability counts.
    """
    if last_release_date is None:
        logger.debug("No release date provided, returning None for age_in_days")
        return None

    # Parse if string
    if isinstance(last_release_date, str):
        release_dt = parse_date(last_release_date)
    elif isinstance(last_release_date, datetime):
        release_dt = last_release_date
    else:
        logger.warning(f"Invalid release_date type: {type(last_release_date)}")
        return None

    if release_dt is None:
        logger.debug("Failed to parse release date, returning None for age_in_days")
        return None

    # Ensure we're working with UTC
    if release_dt.tzinfo is None:
        release_dt = release_dt.replace(tzinfo=timezone.utc)

    now = datetime.now(timezone.utc)
    delta = now - release_dt

    age_days = delta.total_seconds() / (24 * 3600)
    return round(age_days, 2)


def validate_age_data(
    age_in_days: Optional[float],
    vulnerability_count: Optional[int]
) -> dict:
    """
    Validate that age calculation and vulnerability counting are handled correctly
    per FR-010.

    Args:
        age_in_days: The calculated age (can be None for missing release data)
        vulnerability_count: The vulnerability count (should be populated even if age is None)

    Returns:
        dict: Validation results with flags for data quality
    """
    return {
        "age_is_null": age_in_days is None,
        "vulnerability_count_exists": vulnerability_count is not None,
        "fr010_compliant": (age_in_days is None and vulnerability_count is not None) or
                           (age_in_days is not None),
        "message": (
            "FR-010 Compliant: Missing release date handled correctly"
            if age_in_days is None and vulnerability_count is not None else
            "Age data available" if age_in_days is not None else
            "WARNING: Both age and vulnerability count are missing"
        )
    }
