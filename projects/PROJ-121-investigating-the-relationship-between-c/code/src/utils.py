"""
Utility functions for the Cosmic Ray Anisotropy Solar-Cycle Modulation project.
"""
import logging
import sys
import math
from datetime import datetime, timezone
from typing import Optional, Any, Callable


def get_logger(name: str = __name__) -> logging.Logger:
    """
    Get a logger instance with standard configuration.
    
    Args:
        name: Logger name.
        
    Returns:
        Configured logging.Logger instance.
    """
    logger = logging.getLogger(name)
    if not logger.handlers:
        logger.setLevel(logging.INFO)
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    return logger


class PipelineError(Exception):
    """Base exception for pipeline errors."""
    pass


class DataProcessingError(PipelineError):
    """Exception raised during data processing operations."""
    pass


class ConfigurationError(PipelineError):
    """Exception raised for configuration issues."""
    pass


def safe_divide(numerator: float, denominator: float, default: float = 0.0) -> float:
    """
    Safely perform division, returning a default value if denominator is zero.
    
    Args:
        numerator: The dividend.
        denominator: The divisor.
        default: Value to return if division by zero occurs.
        
    Returns:
        Result of division or default value.
    """
    if denominator == 0:
        return default
    return numerator / denominator


def validate_positive(value: float, name: str = "value") -> float:
    """
    Validate that a value is positive.
    
    Args:
        value: Value to validate.
        name: Name of the parameter for error messages.
        
    Returns:
        The validated value.
        
    Raises:
        ValueError: If value is not positive.
    """
    if value <= 0:
        raise ValueError(f"{name} must be positive, got {value}")
    return value


def julian_date(dt: datetime) -> float:
    """
    Convert a datetime object to a UTC Julian Date.
    
    The Julian Date is a continuous count of days since the beginning
    of the Julian Period (January 1, 4713 BC).
    
    Args:
        dt: Datetime object (will be converted to UTC if not already).
        
    Returns:
        Julian Date as a float.
    """
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    else:
        dt = dt.astimezone(timezone.utc)
        
    # Algorithm from Astronomical Algorithms by Jean Meeus
    year = dt.year
    month = dt.month
    day = dt.day + (dt.hour + dt.minute/60.0 + dt.second/3600.0) / 24.0
    
    if month <= 2:
        year -= 1
        month += 12
        
    A = math.floor(year / 100)
    B = 2 - A + math.floor(A / 4)
    
    JD = math.floor(365.25 * (year + 4716)) + \
         math.floor(30.6001 * (month + 1)) + \
         day + B - 1524.5
         
    return JD


def datetime_from_jd(jd: float) -> datetime:
    """
    Convert a Julian Date to a datetime object (UTC).
    
    Args:
        jd: Julian Date as a float.
        
    Returns:
        Datetime object in UTC timezone.
    """
    # Algorithm from Astronomical Algorithms by Jean Meeus
    jd += 0.5
    z = int(jd)
    f = jd - z
    
    if z < 2299161:
        A = z
    else:
        alpha = int((z - 1867216.25) / 36524.25)
        A = z + 1 + alpha - int(alpha / 4)
        
    B = A + 1524
    C = int((B - 122.1) / 365.25)
    D = int(365.25 * C)
    E = int((B - D) / 30.6001)
    
    day = B - D - int(30.6001 * E) + f
    
    if E < 14:
        month = E - 1
    else:
        month = E - 13
        
    if month > 2:
        year = C - 4716
    else:
        year = C - 4715
        
    # Extract time components
    day_int = int(day)
    frac_day = day - day_int
    
    hour = int(frac_day * 24)
    frac_hour = frac_day * 24 - hour
    minute = int(frac_hour * 60)
    frac_minute = frac_hour * 60 - minute
    second = int(frac_minute * 60)
    microsecond = int((frac_minute * 60 - second) * 1e6)
    
    return datetime(year, month, day_int, hour, minute, second, microsecond, tzinfo=timezone.utc)


def log_exceptions(logger: logging.Logger) -> Callable:
    """
    Decorator to log exceptions for a function.
    
    Args:
        logger: Logger instance to use.
        
    Returns:
        Decorator function.
    """
    def decorator(func: Callable) -> Callable:
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                logger.error(f"Exception in {func.__name__}: {str(e)}", exc_info=True)
                raise
        return wrapper
    return decorator
