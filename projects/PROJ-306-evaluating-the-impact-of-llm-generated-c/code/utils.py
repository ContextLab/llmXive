"""Utility functions for the pipeline.

Includes exponential backoff retry logic for API rate limits.
"""
import time
import random
from typing import Callable, TypeVar, Optional, Any, Tuple, Dict
from functools import wraps
import logging

from logger_config import get_logger, log_operation

logger = get_logger("utils")

T = TypeVar('T')

def exponential_backoff_retry(
    func: Callable[..., Tuple[Optional[Any], bool]],
    args: Tuple = (),
    kwargs: Optional[Dict] = None,
    max_attempts: int = 3,
    backoff_factor: float = 2.0,
    initial_wait: float = 1.0
) -> Tuple[Optional[Any], bool]:
    """
    Retry a function with exponential backoff.

    Args:
        func: The function to call. It should return a tuple (result, success).
        args: Arguments to pass to the function.
        kwargs: Keyword arguments to pass to the function.
        max_attempts: Maximum number of attempts.
        backoff_factor: Factor by which the wait time increases (e.g., 2x).
        initial_wait: Initial wait time in seconds.

    Returns:
        Tuple of (result, success). If all attempts fail, returns (None, False).
    """
    if kwargs is None:
        kwargs = {}

    wait_time = initial_wait
    last_error = None

    for attempt in range(1, max_attempts + 1):
        try:
            result, success = func(*args, **kwargs)
            if success:
                return result, True
            else:
                # Function returned failure (e.g., API error, invalid response)
                # If it's a specific error type (like 429), we retry.
                # For simplicity, we treat non-success as retryable here if attempts remain.
                last_error = "Function returned failure"
                if attempt < max_attempts:
                    logger.log("retrying_function", attempt=attempt, max=max_attempts, wait=wait_time)
                    time.sleep(wait_time)
                    wait_time *= backoff_factor
                else:
                    logger.log("max_retries_exceeded", func_name=func.__name__, error=last_error)
                    return None, False
        except Exception as e:
            last_error = str(e)
            logger.log("exception_in_retry", attempt=attempt, max=max_attempts, error=last_error)
            if attempt < max_attempts:
                logger.log("retrying_after_exception", wait=wait_time)
                time.sleep(wait_time)
                wait_time *= backoff_factor
            else:
                logger.log("max_retries_exceeded_exception", func_name=func.__name__, error=last_error)
                return None, False

    return None, False

def retry_with_backoff(
    func: Callable[..., T],
    max_attempts: int = 3,
    backoff_factor: float = 2.0,
    initial_wait: float = 1.0
) -> Callable[..., T]:
    """
    Decorator to add retry logic with exponential backoff to a function.
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        return exponential_backoff_retry(func, args, kwargs, max_attempts, backoff_factor, initial_wait)
    return wrapper

def safe_get(d: Dict, key: str, default: Any = None) -> Any:
    """Safely get a value from a dictionary."""
    return d.get(key, default)

def format_bytes(num_bytes: int) -> str:
    """Format bytes into human-readable string."""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if abs(num_bytes) < 1024.0:
            return f"{num_bytes:.2f} {unit}"
        num_bytes /= 1024.0
    return f"{num_bytes:.2f} PB"
