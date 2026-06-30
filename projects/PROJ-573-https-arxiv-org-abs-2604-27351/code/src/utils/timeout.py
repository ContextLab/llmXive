"""
Timeout enforcement utilities for benchmark tasks.

Implements FR-006 and FR-013: enforce execution timeouts and raise TimeoutError
if the limit is exceeded.
"""

import signal
import threading
import time
from functools import wraps
from typing import Callable, Any, Optional, Union
import logging

from .logging import get_logger

logger = get_logger(__name__)


class TimeoutError(Exception):
    """Custom TimeoutError for benchmark task timeouts."""
    pass


def enforce_timeout(func: Callable, timeout_seconds: int = 300) -> Callable:
    """
    Decorator to enforce a timeout on a function execution.

    If the function does not complete within timeout_seconds, a TimeoutError
    is raised.

    Args:
        func: The function to wrap.
        timeout_seconds: Maximum allowed execution time in seconds.

    Returns:
        Wrapped function that enforces the timeout.
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        result = [None]
        exception = [None]

        def target():
            try:
                result[0] = func(*args, **kwargs)
            except Exception as e:
                exception[0] = e

        thread = threading.Thread(target=target)
        thread.daemon = True
        thread.start()
        thread.join(timeout=timeout_seconds)

        if thread.is_alive():
            logger.error(f"Function {func.__name__} exceeded timeout of {timeout_seconds}s")
            raise TimeoutError(f"Function {func.__name__} timed out after {timeout_seconds} seconds")

        if exception[0] is not None:
            raise exception[0]

        return result[0]

    return wrapper


def run_with_timeout(
    func: Callable,
    args: tuple = (),
    kwargs: Optional[dict] = None,
    timeout_seconds: int = 300
) -> Any:
    """
    Execute a function with a timeout.

    This is a functional alternative to the decorator for cases where
    dynamic timeout configuration is needed.

    Args:
        func: The function to execute.
        args: Positional arguments for the function.
        kwargs: Keyword arguments for the function.
        timeout_seconds: Maximum allowed execution time in seconds.

    Returns:
        The result of the function if it completes in time.

    Raises:
        TimeoutError: If the function exceeds the timeout.
    """
    if kwargs is None:
        kwargs = {}

    result = [None]
    exception = [None]

    def target():
        try:
            result[0] = func(*args, **kwargs)
        except Exception as e:
            exception[0] = e

    thread = threading.Thread(target=target)
    thread.daemon = True
    thread.start()
    thread.join(timeout=timeout_seconds)

    if thread.is_alive():
        logger.error(f"Function {func.__name__} exceeded timeout of {timeout_seconds}s")
        raise TimeoutError(f"Function {func.__name__} timed out after {timeout_seconds} seconds")

    if exception[0] is not None:
        raise exception[0]

    return result[0]


def main():
    """
    Demonstration of timeout enforcement.
    """
    import sys

    def slow_function(duration: float):
        time.sleep(duration)
        return "Completed"

    def fast_function(duration: float):
        time.sleep(duration)
        return "Fast Completed"

    # Test 1: Function completes within timeout
    logger.info("Test 1: Fast function with 5s timeout")
    try:
        result = run_with_timeout(fast_function, args=(1.0,), timeout_seconds=5)
        logger.info(f"Result: {result}")
    except TimeoutError as e:
        logger.error(f"Unexpected timeout: {e}")
        sys.exit(1)

    # Test 2: Function exceeds timeout
    logger.info("Test 2: Slow function with 1s timeout (should timeout)")
    try:
        result = run_with_timeout(slow_function, args=(3.0,), timeout_seconds=1)
        logger.error(f"Should have timed out but got: {result}")
        sys.exit(1)
    except TimeoutError as e:
        logger.info(f"Expected timeout caught: {e}")

    logger.info("All timeout tests passed.")


if __name__ == "__main__":
    main()