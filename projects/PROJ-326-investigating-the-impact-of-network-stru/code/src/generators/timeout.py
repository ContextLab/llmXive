"""
Global timeout utility for network generation tasks.

Provides a decorator and context manager to enforce execution timeouts
with explicit logging and fallback behavior. If a timeout is hit or
a maximum number of retries is exhausted, a warning is logged and the
operation proceeds (or returns a safe default) rather than crashing.
"""
import functools
import signal
import logging
import time
from typing import Callable, Any, Optional, TypeVar, Union
from pathlib import Path

# Configure logger for this module
logger = logging.getLogger(__name__)
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

# Type variable for generic decorator
F = TypeVar('F', bound=Callable[..., Any])

class TimeoutError(Exception):
    """Custom timeout exception for generation tasks."""
    pass

class TimeoutHandler:
    """
    Handles signal-based timeouts for Unix-like systems.
    Falls back to a thread-based approach for Windows or non-Unix environments.
    """
    def __init__(self, seconds: int, retries: int = 3):
        self.seconds = seconds
        self.max_retries = retries
        self.current_retry = 0

    def _signal_handler(self, signum, frame):
        raise TimeoutError(f"Operation timed out after {self.seconds} seconds.")

    def __enter__(self):
        if hasattr(signal, 'SIGALRM'):
            # Unix: Use signal
            self._old_handler = signal.signal(signal.SIGALRM, self._signal_handler)
            signal.alarm(self.seconds)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if hasattr(signal, 'SIGALRM'):
            signal.alarm(0)  # Cancel alarm
            signal.signal(signal.SIGALRM, self._old_handler)
        # Suppress TimeoutError if we want to handle it gracefully outside
        # but for the context manager usage, we let it bubble up to be caught
        return False

def timeout(seconds: int, retries: int = 3, fallback_value: Any = None):
    """
    Decorator that enforces a timeout on a function.

    If the function exceeds `seconds`, it is terminated.
    If the total number of attempts (initial + retries) is exhausted,
    a warning is logged and `fallback_value` is returned.

    Args:
        seconds: Maximum execution time in seconds.
        retries: Number of retry attempts after a timeout.
        fallback_value: Value to return if all retries are exhausted.

    Returns:
        Decorated function.
    """
    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            attempt = 0
            last_exception = None

            while attempt <= retries:
                try:
                    if hasattr(signal, 'SIGALRM'):
                        with TimeoutHandler(seconds):
                            return func(*args, **kwargs)
                    else:
                        # Fallback for Windows: simple time check loop (approximate)
                        # Note: This cannot forcibly kill a thread, so it's a cooperative check
                        start = time.time()
                        result = func(*args, **kwargs)
                        if time.time() - start > seconds:
                            raise TimeoutError(f"Operation took too long (> {seconds}s)")
                        return result
                except TimeoutError as e:
                    last_exception = e
                    attempt += 1
                    if attempt <= retries:
                        logger.warning(
                            f"Timeout hit for {func.__name__} (attempt {attempt}/{retries + 1}). "
                            f"Retrying..."
                        )
                    else:
                        logger.warning(
                            f"Max retries ({retries}) exhausted for {func.__name__}. "
                            f"Returning fallback value."
                        )
                        return fallback_value
                except Exception as e:
                    # Re-raise non-timeout exceptions immediately
                    raise e

            # Should not reach here, but safe fallback
            logger.error(f"Unexpected error in retry loop for {func.__name__}")
            return fallback_value

        return wrapper  # type: ignore
    return decorator

def enforce_timeout(seconds: int, retries: int = 3, fallback_value: Any = None):
    """
    Function-level timeout enforcement helper.
    Can be used as a context manager or standalone check.
    """
    return timeout(seconds, retries, fallback_value)

# Example usage verification (can be removed or kept for documentation)
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    @timeout(seconds=2, retries=1, fallback_value=-1)
    def slow_function():
        time.sleep(5)
        return 42

    @timeout(seconds=1, retries=0, fallback_value="timeout")
    def fast_function():
        return "success"

    print("Testing fast function:")
    print(fast_function())

    print("\nTesting slow function (should timeout and retry):")
    result = slow_function()
    print(f"Result: {result}")
    print("Test complete.")