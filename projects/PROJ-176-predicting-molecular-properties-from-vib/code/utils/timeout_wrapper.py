"""
Timeout wrapper utilities to enforce strict runtime limits.
Implements FR-006 for time-bounded execution.
"""
import signal
import time
from contextlib import contextmanager
from functools import wraps
from typing import Callable, Optional

class TimeoutError(Exception):
    """Exception raised when a timeout occurs."""
    pass

@contextmanager
def timeout_context(seconds: int):
    """
    Context manager that raises TimeoutError if the block exceeds the time limit.

    Args:
        seconds: Maximum allowed execution time in seconds.

    Raises:
        TimeoutError: If the block execution exceeds the time limit.
    """
    if seconds <= 0:
        yield
        return

    def timeout_handler(signum, frame):
        raise TimeoutError(f"Operation timed out after {seconds} seconds")

    # Set the signal handler
    old_handler = signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(seconds)

    try:
        yield
    finally:
        # Reset the alarm and restore the old handler
        signal.alarm(0)
        signal.signal(signal.SIGALRM, old_handler)

def timeout_decorator(seconds: int):
    """
    Decorator that enforces a timeout on a function.

    Args:
        seconds: Maximum allowed execution time in seconds.

    Returns:
        Decorated function that raises TimeoutError if it exceeds the time limit.
    """
    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            with timeout_context(seconds):
                return func(*args, **kwargs)
        return wrapper
    return decorator

def enforce_timeout(
    func: Callable,
    seconds: int,
    timeout_message: Optional[str] = None
) -> Callable:
    """
    Wrap a function to enforce a timeout.

    Args:
        func: Function to wrap.
        seconds: Maximum allowed execution time in seconds.
        timeout_message: Custom message for TimeoutError.

    Returns:
        Wrapped function that enforces the timeout.
    """
    if timeout_message is None:
        timeout_message = f"Function {func.__name__} timed out after {seconds} seconds"

    @wraps(func)
    def wrapper(*args, **kwargs):
        with timeout_context(seconds):
            try:
                return func(*args, **kwargs)
            except TimeoutError:
                raise TimeoutError(timeout_message)
    return wrapper
