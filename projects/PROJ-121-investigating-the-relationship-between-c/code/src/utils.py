"""
Utility functions for the cosmic ray anisotropy analysis pipeline.

Includes logging, date conversions, and mathematical helpers.
"""
import logging
import sys
from datetime import datetime, timezone
from typing import Optional
import math

# Constants for Julian date calculation
# Julian Date epoch: January 1, 4713 BC, noon UTC
JD_EPOCH = 1721424.5
# Days from 2000-01-01 12:00:00 UTC to JD epoch
JD_2000 = 2451545.0


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance with the specified name.

    Args:
        name: Logger name (usually __name__).

    Returns:
        Configured logging.Logger instance.
    """
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    return logger


def julian_date(dt: datetime) -> float:
    """
    Convert a datetime object to Julian Date (UTC).

    The Julian Date is a continuous count of days since January 1, 4713 BC, noon UTC.

    Args:
        dt: datetime object (timezone-aware, will be converted to UTC).

    Returns:
        Julian Date as a float.
    """
    if dt.tzinfo is None:
        # Assume UTC if timezone-naive
        dt = dt.replace(tzinfo=timezone.utc)
    else:
        dt = dt.astimezone(timezone.utc)

    # Convert to ordinal days since 0001-01-01
    # datetime.toordinal() returns days since 0001-01-01 (proleptic Gregorian)
    days_since_epoch = dt.toordinal() - 1 + JD_EPOCH

    # Add fractional day from time
    seconds_in_day = 86400.0
    seconds_today = (dt.hour * 3600 + dt.minute * 60 + dt.second + dt.microsecond / 1e6)
    fractional_day = seconds_today / seconds_in_day

    jd = days_since_epoch + fractional_day - 0.5  # Julian day starts at noon

    return jd


def datetime_from_jd(jd: float) -> datetime:
    """
    Convert a Julian Date back to a datetime object (UTC).

    Args:
        jd: Julian Date as a float.

    Returns:
        timezone-aware datetime object in UTC.
    """
    # Julian Date to days since 0001-01-01
    days_since_epoch = jd - JD_EPOCH + 0.5

    # Integer days
    integer_days = int(days_since_epoch)
    fractional_day = days_since_epoch - integer_days

    # Convert to datetime
    dt = datetime.fromordinal(integer_days + 1)

    # Add fractional day
    seconds_in_day = 86400.0
    total_seconds = int(fractional_day * seconds_in_day)
    microseconds = int((fractional_day * seconds_in_day - total_seconds) * 1e6)

    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    seconds = total_seconds % 60

    dt = dt.replace(
        hour=hours,
        minute=minutes,
        second=seconds,
        microsecond=microseconds,
        tzinfo=timezone.utc
    )

    return dt


def safe_divide(numerator: float, denominator: float, default: float = 0.0) -> float:
    """
    Safely divide two numbers, returning a default if division by zero occurs.

    Args:
        numerator: The numerator.
        denominator: The denominator.
        default: Value to return if denominator is zero.

    Returns:
        The result of numerator / denominator, or default.
    """
    if denominator == 0:
        return default
    return numerator / denominator


def validate_positive(value: float, name: str = "value") -> float:
    """
    Validate that a value is positive.

    Args:
        value: The value to check.
        name: Name of the value for error messages.

    Returns:
        The value if positive.

    Raises:
        ValueError: If the value is not positive.
    """
    if value <= 0:
        raise ValueError(f"{name} must be positive, got {value}")
    return value
