"""
Timeout enforcement utilities for benchmark tasks.

Provides context managers and decorators to enforce execution time limits
on task functions, raising TimeoutError if the limit is exceeded.

FR-006, FR-013
"""

import signal
import threading
import time
from functools import wraps
from typing import Callable, Any, Optional, Union
import logging

from src.utils.logging import get_logger

logger = get_logger(__name__)

# Custom TimeoutError that inherits from built-in TimeoutError for compatibility
# but allows specific identification if needed
class TimeoutError(Exception):
    """Raised when a task exceeds its allowed execution time."""
    pass

def _timeout_handler(signum, frame):
    """Signal handler for Unix-based timeout enforcement."""
    raise TimeoutError("Task execution exceeded the allowed timeout.")

def run_with_timeout(func: Callable, timeout_seconds: int = 300, *args, **kwargs) -> Any:
    """
    Run a function with a hard timeout.

    Uses signal-based timeout on Unix systems (SIGALRM) and threading-based
    timeout on Windows or when signal handling is not available.

    Args:
        func: The function to execute.
        timeout_seconds: Maximum allowed execution time in seconds.
        *args: Positional arguments to pass to the function.
        **kwargs: Keyword arguments to pass to the function.

    Returns:
        The return value of the function if it completes within the timeout.

    Raises:
        TimeoutError: If the function exceeds the timeout.
        Exception: Any exception raised by the function itself.
    """
    # Try signal-based approach for Unix systems
    if hasattr(signal, 'SIGALRM') and hasattr(signal, 'alarm'):
        # Set up the signal handler
        old_handler = signal.signal(signal.SIGALRM, _timeout_handler)
        # Set the alarm
        signal.alarm(timeout_seconds)
        try:
            result = func(*args, **kwargs)
            return result
        except TimeoutError:
            logger.error(f"Function {func.__name__} timed out after {timeout_seconds}s")
            raise
        finally:
            # Cancel the alarm and restore the old handler
            signal.alarm(0)
            signal.signal(signal.SIGALRM, old_handler)
    else:
        # Fallback to threading-based timeout for Windows or environments without SIGALRM
        result_container = {'result': None, 'exception': None}
        completed = threading.Event()

        def target():
            try:
                result_container['result'] = func(*args, **kwargs)
            except Exception as e:
                result_container['exception'] = e
            finally:
                completed.set()

        thread = threading.Thread(target=target)
        thread.daemon = True
        thread.start()

        if not completed.wait(timeout=timeout_seconds):
            logger.error(f"Function {func.__name__} timed out after {timeout_seconds}s (threading fallback)")
            raise TimeoutError(f"Function {func.__name__} exceeded timeout of {timeout_seconds}s")

        if result_container['exception'] is not None:
            raise result_container['exception']

        return result_container['result']

def enforce_timeout(func: Callable, timeout_seconds: int = 300) -> Callable:
    """
    Decorator to enforce a timeout on a function.

    Wraps the function so that calling it will raise TimeoutError if
    execution exceeds the specified duration.

    Args:
        func: The function to wrap.
        timeout_seconds: Maximum allowed execution time in seconds.

    Returns:
        A wrapped function that enforces the timeout.
    """
    @wraps(func)
    def wrapper(*args, **kwargs) -> Any:
        return run_with_timeout(func, timeout_seconds, *args, **kwargs)
    return wrapper

def main():
    """Test script for timeout enforcement."""
    import sys

    def slow_function(duration: float) -> str:
        """Simulates a slow computation."""
        time.sleep(duration)
        return "Completed successfully"

    def fast_function() -> str:
        """Simulates a fast computation."""
        return "Fast result"

    logger.info("Testing timeout enforcement...")

    # Test 1: Function completes within timeout
    logger.info("Test 1: Fast function with 5s timeout")
    try:
        result = run_with_timeout(fast_function, timeout_seconds=5)
        logger.info(f"  Result: {result}")
        logger.info("  Status: PASSED")
    except TimeoutError:
        logger.error("  Status: FAILED - Unexpected timeout")
        sys.exit(1)

    # Test 2: Function exceeds timeout
    logger.info("Test 2: Slow function (3s) with 1s timeout")
    try:
        result = run_with_timeout(slow_function, timeout_seconds=1, duration=3)
        logger.error("  Status: FAILED - Should have timed out")
        sys.exit(1)
    except TimeoutError as e:
        logger.info(f"  Caught expected TimeoutError: {e}")
        logger.info("  Status: PASSED")

    # Test 3: Decorator usage
    logger.info("Test 3: Decorator usage")
    decorated_func = enforce_timeout(fast_function, timeout_seconds=5)
    try:
        result = decorated_func()
        logger.info(f"  Result: {result}")
        logger.info("  Status: PASSED")
    except TimeoutError:
        logger.error("  Status: FAILED - Unexpected timeout")
        sys.exit(1)

    logger.info("All timeout tests passed.")

if __name__ == "__main__":
    main()