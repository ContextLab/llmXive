"""
Timeout utilities for enforcing API and test execution limits.

Provides decorators and context managers to enforce:
- 120s timeout for API calls (T009 requirement)
- 10s timeout for test execution (T009 requirement)
"""

import signal
import time
from functools import wraps
from typing import Callable, Any, Optional, Type


class TimeoutError(Exception):
    """Custom exception raised when a timeout occurs."""
    pass


class TimeoutHandler:
    """
    Handler for signal-based timeouts.

    Raises a custom TimeoutError when the signal is received.
    """

    def __init__(self, seconds: int, error_message: Optional[str] = None):
        self.seconds = seconds
        self.error_message = error_message or f"Operation timed out after {seconds} seconds"
        self.old_handler = None

    def __call__(self, signum, frame):
        raise TimeoutError(self.error_message)

    def __enter__(self):
        # Set the signal handler
        self.old_handler = signal.signal(signal.SIGALRM, self)
        # Start the alarm
        signal.alarm(self.seconds)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        # Cancel the alarm
        signal.alarm(0)
        # Restore the old handler
        if self.old_handler is not None:
            signal.signal(signal.SIGALRM, self.old_handler)
        # Don't suppress the exception
        return False


def enforce_api_timeout(func: Callable) -> Callable:
    """
    Decorator to enforce a 120-second timeout on API calls.

    Args:
        func: The function to wrap.

    Returns:
        The wrapped function with timeout enforcement.
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        with TimeoutHandler(seconds=120, error_message="API call timed out after 120 seconds"):
            return func(*args, **kwargs)
    return wrapper


def enforce_test_timeout(func: Callable) -> Callable:
    """
    Decorator to enforce a 10-second timeout on test execution.

    Args:
        func: The function to wrap.

    Returns:
        The wrapped function with timeout enforcement.
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        with TimeoutHandler(seconds=10, error_message="Test execution timed out after 10 seconds"):
            return func(*args, **kwargs)
    return wrapper


def run_with_api_timeout(func: Callable, *args, timeout: int = 120, **kwargs) -> Any:
    """
    Helper function to run a function with an API timeout.

    Args:
        func: The function to run.
        *args: Positional arguments to pass to the function.
        timeout: Timeout in seconds (default: 120).
        **kwargs: Keyword arguments to pass to the function.

    Returns:
        The result of the function.

    Raises:
        TimeoutError: If the function execution exceeds the timeout.
    """
    with TimeoutHandler(seconds=timeout):
        return func(*args, **kwargs)


def run_with_test_timeout(func: Callable, *args, timeout: int = 10, **kwargs) -> Any:
    """
    Helper function to run a function with a test timeout.

    Args:
        func: The function to run.
        *args: Positional arguments to pass to the function.
        timeout: Timeout in seconds (default: 10).
        **kwargs: Keyword arguments to pass to the function.

    Returns:
        The result of the function.

    Raises:
        TimeoutError: If the function execution exceeds the timeout.
    """
    with TimeoutHandler(seconds=timeout):
        return func(*args, **kwargs)