"""
Timeout enforcement utilities for benchmark tasks.

Provides functions to enforce execution timeouts on callable functions,
raising TimeoutError if the execution exceeds the specified duration.
"""

import signal
import threading
import time
from functools import wraps
from typing import Callable, Any, Optional, Union
import logging

from src.utils.logging import get_logger

logger = get_logger(__name__)

class TimeoutError(Exception):
    """Custom exception raised when a function execution exceeds the timeout."""
    pass


def enforce_timeout(func: Callable, timeout_seconds: float = 300) -> Callable:
    """
    Decorator to enforce a timeout on a function execution.

    Args:
        func: The function to wrap with timeout logic.
        timeout_seconds: Maximum allowed execution time in seconds (default: 300).

    Returns:
        A wrapped function that raises TimeoutError if execution exceeds timeout.

    Raises:
        TimeoutError: If the function execution exceeds timeout_seconds.
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        result = [None]
        exception = [None]
        thread_exception = None

        def target():
            try:
                result[0] = func(*args, **kwargs)
            except Exception as e:
                exception[0] = e

        # Use threading to enforce timeout without signal limitations
        thread = threading.Thread(target=target)
        thread.daemon = True
        thread.start()
        thread.join(timeout=timeout_seconds)

        if thread.is_alive():
            logger.warning(f"Function {func.__name__} exceeded timeout of {timeout_seconds}s")
            raise TimeoutError(
                f"Function '{func.__name__}' exceeded timeout of {timeout_seconds} seconds"
            )

        thread.join()

        if exception[0] is not None:
            raise exception[0]

        return result[0]

    return wrapper


def run_with_timeout(
    func: Callable,
    timeout_seconds: float = 300,
    *args,
    **kwargs
) -> Any:
    """
    Execute a function with a timeout, returning the result or raising TimeoutError.

    This is an alternative to the decorator approach for one-off executions.

    Args:
        func: The function to execute.
        timeout_seconds: Maximum allowed execution time in seconds.
        *args: Positional arguments to pass to func.
        **kwargs: Keyword arguments to pass to func.

    Returns:
        The return value of func if it completes within timeout.

    Raises:
        TimeoutError: If the function execution exceeds timeout_seconds.
        Any exception raised by func if it occurs before timeout.
    """
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
        logger.warning(f"Function {func.__name__} exceeded timeout of {timeout_seconds}s")
        raise TimeoutError(
            f"Function '{func.__name__}' exceeded timeout of {timeout_seconds} seconds"
        )

    thread.join()

    if exception[0] is not None:
        raise exception[0]

    return result[0]


def main():
    """
    Demonstration of timeout enforcement functionality.
    """
    logger.info("Testing timeout enforcement module...")

    # Test 1: Function that completes within timeout
    def quick_task():
        time.sleep(0.1)
        return "success"

    try:
        result = run_with_timeout(quick_task, timeout_seconds=5)
        logger.info(f"Test 1 passed: {result}")
    except TimeoutError as e:
        logger.error(f"Test 1 failed: {e}")

    # Test 2: Function that exceeds timeout
    def slow_task():
        time.sleep(10)
        return "should not reach here"

    try:
        result = run_with_timeout(slow_task, timeout_seconds=1)
        logger.error("Test 2 failed: Should have raised TimeoutError")
    except TimeoutError as e:
        logger.info(f"Test 2 passed: {e}")

    # Test 3: Decorator usage
    @enforce_timeout(timeout_seconds=2)
    def decorated_task():
        time.sleep(0.5)
        return "decorated success"

    try:
        result = decorated_task()
        logger.info(f"Test 3 passed: {result}")
    except TimeoutError as e:
        logger.error(f"Test 3 failed: {e}")

    logger.info("Timeout enforcement tests completed.")


if __name__ == "__main__":
    main()