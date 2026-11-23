"""
Utility module for enforcing system limits (timeouts, memory) on operations.

This module implements the internal timeout wrapper required by FR-007,
using signal handling to abort long-running operations immediately.
It provides a retry loop with per-attempt timeouts and a total timeout guard.
"""

import os
import signal
import sys
import resource
import logging
import time
from functools import wraps
from contextlib import contextmanager
from typing import Callable, Any, Optional, List
from pathlib import Path

logger = logging.getLogger(__name__)

# Default timeouts as per task specification
DEFAULT_PER_ATTEMPT_TIMEOUT = 100  # seconds
DEFAULT_TOTAL_RETRY_TIMEOUT = 300  # seconds
MAX_RETRIES = 3
RETRY_INTERVAL = 10  # seconds

class TimeoutError(Exception):
    """Exception raised when an operation exceeds its timeout limit."""
    pass

class MemoryLimitError(Exception):
    """Exception raised when an operation exceeds its memory limit."""
    pass

def _signal_handler(signum, frame):
    """Internal signal handler for SIGALRM."""
    raise TimeoutError("Operation exceeded the per-attempt timeout limit.")

def _total_timeout_handler(signum, frame):
    """Signal handler for total timeout."""
    logger.critical("Total retry timeout exceeded. Terminating pipeline.")
    os._exit(1)

def timeout_guard(func: Callable, timeout: Optional[int] = None):
    """
    Decorator to enforce a timeout on a function using signal handling.

    This implements the "immediate abort" constraint for slow operations like
    network retries. If the function takes longer than the specified timeout,
    a TimeoutError is raised.

    Args:
        func: The function to wrap.
        timeout: Timeout in seconds. If None, uses a default or config.

    Returns:
        Wrapped function that enforces the timeout.
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        # Determine the timeout threshold
        operation_timeout = timeout if timeout is not None else DEFAULT_PER_ATTEMPT_TIMEOUT

        if sys.platform.startswith('win'):
            logger.warning(
                "Signal-based timeouts are not supported on Windows. "
                "The timeout_guard decorator will be skipped."
            )
            return func(*args, **kwargs)

        old_handler = signal.signal(signal.SIGALRM, _signal_handler)
        signal.alarm(operation_timeout)

        try:
            result = func(*args, **kwargs)
        finally:
            signal.alarm(0)
            signal.signal(signal.SIGALRM, old_handler)

        return result

    return wrapper

@contextmanager
def timeout_context(timeout: Optional[int] = None):
    """
    Context manager to enforce a timeout on a block of code.

    Args:
        timeout: Timeout in seconds. If None, uses a default.

    Yields:
        None

    Raises:
        TimeoutError: If the block exceeds the timeout.
    """
    operation_timeout = timeout if timeout is not None else DEFAULT_PER_ATTEMPT_TIMEOUT

    if sys.platform.startswith('win'):
        logger.warning(
            "Signal-based timeouts are not supported on Windows. "
            "The timeout_context will be skipped."
        )
        yield
        return

    old_handler = signal.signal(signal.SIGALRM, _signal_handler)
    signal.alarm(operation_timeout)

    try:
        yield
    finally:
        signal.alarm(0)
        signal.signal(signal.SIGALRM, old_handler)

def retry_with_timeout(
    func: Callable,
    per_attempt_timeout: int = DEFAULT_PER_ATTEMPT_TIMEOUT,
    total_retry_timeout: int = DEFAULT_TOTAL_RETRY_TIMEOUT,
    max_retries: int = MAX_RETRIES,
    retry_interval: int = RETRY_INTERVAL,
    *args,
    **kwargs
) -> Any:
    """
    Execute a function with a retry loop, enforcing per-attempt and total timeouts.

    This implements the core logic for FR-007:
    1. Attempts to run `func` up to `max_retries` times.
    2. Each attempt is wrapped in a `per_attempt_timeout`.
    3. If an attempt fails due to TimeoutError, it waits `retry_interval` and retries.
    4. If the total elapsed time exceeds `total_retry_timeout`, it triggers `os._exit(1)`.
    5. If all retries are exhausted and total time is still within limit, it raises the last exception.

    Args:
        func: The function to execute.
        per_attempt_timeout: Timeout for a single attempt (seconds).
        total_retry_timeout: Maximum total time for all attempts (seconds).
        max_retries: Maximum number of attempts.
        retry_interval: Seconds to wait between attempts.
        *args: Positional arguments for `func`.
        **kwargs: Keyword arguments for `func`.

    Returns:
        The result of `func` if successful.

    Raises:
        TimeoutError: If all retries fail and total timeout not exceeded.
        SystemExit: If total timeout is exceeded.
    """
    start_time = time.time()
    last_exception = None

    # Set up the total timeout handler
    if not sys.platform.startswith('win'):
        old_total_handler = signal.signal(signal.SIGALRM, _total_timeout_handler)
        signal.alarm(total_retry_timeout)
    else:
        old_total_handler = None
        logger.warning("Total timeout check via signal not available on Windows. "
                     "Will check elapsed time manually.")

    try:
        for attempt in range(1, max_retries + 1):
            # Check total timeout before each attempt
            elapsed = time.time() - start_time
            if elapsed > total_retry_timeout:
                logger.critical(f"Total retry timeout ({total_retry_timeout}s) exceeded before attempt {attempt}.")
                if not sys.platform.startswith('win'):
                    os._exit(1)
                else:
                    raise TimeoutError(f"Total retry timeout exceeded: {elapsed:.2f}s > {total_retry_timeout}s")

            logger.info(f"Attempt {attempt}/{max_retries} for '{func.__name__}'...")
            try:
                if sys.platform.startswith('win'):
                    # Fallback for Windows: manual time check inside a loop is hard,
                    # but we can wrap the call and check time after.
                    # For strict per-attempt timeout on Windows, we rely on the function's internal logic
                    # or accept that this specific signal-based feature is degraded.
                    # However, we must still respect the total timeout.
                    result = func(*args, **kwargs)
                    return result
                else:
                    with timeout_context(timeout=per_attempt_timeout):
                        result = func(*args, **kwargs)
                    return result
            except TimeoutError as e:
                last_exception = e
                logger.warning(f"Attempt {attempt} timed out: {e}. "
                             f"Retrying in {retry_interval}s...")
                # Sleep but be careful not to exceed total timeout
                sleep_start = time.time()
                while time.time() - sleep_start < retry_interval:
                    if time.time() - start_time > total_retry_timeout:
                        logger.critical("Total timeout exceeded during retry wait.")
                        os._exit(1)
                    time.sleep(0.1) # Short sleep to allow total timeout check
            except Exception as e:
                # Non-timeout errors are retried immediately or logged?
                # Task says: "If a single attempt exceeds per_attempt_timeout, it is retried."
                # It doesn't explicitly say other errors are retried, but usually retry loops catch all.
                # We will log and retry for robustness, unless it's a fatal error.
                last_exception = e
                logger.warning(f"Attempt {attempt} failed with error: {e}. Retrying in {retry_interval}s...")
                time.sleep(retry_interval)

        # If we reach here, all retries failed
        logger.error(f"All {max_retries} attempts failed for '{func.__name__}'.")
        raise last_exception if last_exception else TimeoutError("Unknown failure")

    finally:
        # Cancel total timeout alarm
        if not sys.platform.startswith('win'):
            signal.alarm(0)
            signal.signal(signal.SIGALRM, old_total_handler)

def get_memory_usage_mb() -> float:
    """
    Get the current memory usage of the process in MB.

    Returns:
        Memory usage in megabytes.
    """
    if sys.platform.startswith('win'):
        try:
            import psutil
            process = psutil.Process(os.getpid())
            return process.memory_info().rss / (1024 * 1024)
        except ImportError:
            return 0.0
    else:
        usage = resource.getrusage(resource.RUSAGE_SELF)
        maxrss = usage.ru_maxrss
        if sys.platform == 'darwin':
            return maxrss / (1024 * 1024)
        else:
            return maxrss / 1024.0

def check_memory_usage(limit_gb: float = 7.0) -> bool:
    """
    Check if current memory usage is within the specified limit.

    Args:
        limit_gb: Memory limit in gigabytes.

    Returns:
        True if within limit, False otherwise.
    """
    current_mb = get_memory_usage_mb()
    limit_mb = limit_gb * 1024
    return current_mb <= limit_mb

def memory_guard(func: Callable, limit_gb: float = 7.0):
    """
    Decorator to enforce a memory limit on a function.

    Args:
        func: The function to wrap.
        limit_gb: Memory limit in gigabytes.

    Returns:
        Wrapped function that checks memory usage.
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            result = func(*args, **kwargs)
            if not check_memory_usage(limit_gb):
                raise MemoryLimitError(
                    f"Operation '{func.__name__}' exceeded memory limit of {limit_gb}GB. "
                    f"Current usage: {get_memory_usage_mb():.2f}MB"
                )
            return result
        except MemoryLimitError:
            raise
        except Exception as e:
            raise
    return wrapper
