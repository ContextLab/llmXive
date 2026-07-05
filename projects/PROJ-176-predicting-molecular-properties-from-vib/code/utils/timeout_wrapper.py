"""
Timeout wrapper module to enforce strict runtime limits (FR-006).

This module provides a context manager and a decorator to enforce
a maximum execution time for code blocks or functions. If the time
limit is exceeded, a TimeoutError is raised.
"""

import signal
import time
from contextlib import contextmanager
from functools import wraps
from typing import Callable, Optional


class TimeoutError(RuntimeError):
    """Custom exception raised when a timeout occurs."""
    pass


@contextmanager
def timeout_context(seconds: int, message: Optional[str] = None):
    """
    Context manager to enforce a time limit on a block of code.

    Args:
        seconds (int): Maximum allowed execution time in seconds.
        message (str, optional): Custom error message. Defaults to generic timeout message.

    Raises:
        TimeoutError: If the execution time exceeds the specified limit.
    """
    if seconds <= 0:
        raise ValueError("Timeout seconds must be positive.")

    # Define the signal handler
    def handler(signum, frame):
        raise TimeoutError(message or f"Operation timed out after {seconds} seconds.")

    # Set the signal handler and alarm
    old_handler = signal.signal(signal.SIGALRM, handler)
    signal.alarm(seconds)

    try:
        yield
    finally:
        # Restore the old handler and cancel the alarm
        signal.alarm(0)
        signal.signal(signal.SIGALRM, old_handler)


def timeout_decorator(seconds: int, message: Optional[str] = None):
    """
    Decorator to enforce a time limit on a function.

    Args:
        seconds (int): Maximum allowed execution time in seconds.
        message (str, optional): Custom error message. Defaults to generic timeout message.

    Returns:
        Callable: The wrapped function with timeout enforcement.
    """
    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            with timeout_context(seconds, message):
                return func(*args, **kwargs)
        return wrapper
    return decorator


def enforce_timeout(func: Callable, seconds: int):
    """
    Convenience function to run a function with a timeout.

    Args:
        func (Callable): The function to execute.
        seconds (int): Maximum allowed execution time in seconds.

    Returns:
        Any: The return value of the function if it completes in time.

    Raises:
        TimeoutError: If the function execution exceeds the time limit.
    """
    with timeout_context(seconds):
        return func()