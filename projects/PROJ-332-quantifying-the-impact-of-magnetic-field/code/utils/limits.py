"""
Utility module for enforcing system limits (timeouts, memory) on operations.

This module implements the internal timeout wrapper required by FR-007,
using signal handling to abort long-running operations immediately.
"""

import os
import signal
import sys
import resource
import logging
from functools import wraps
from contextlib import contextmanager
from typing import Callable, Any, Optional
from pathlib import Path

# Import the configurable timeout constant
from code.config import PER_OPERATION_TIMEOUT

logger = logging.getLogger(__name__)

class TimeoutError(Exception):
    """Exception raised when an operation exceeds its timeout limit."""
    pass

class MemoryLimitError(Exception):
    """Exception raised when an operation exceeds its memory limit."""
    pass

def timeout_guard(func: Callable, timeout: Optional[int] = None):
    """
    Decorator to enforce a timeout on a function using signal handling.

    This implements the "immediate abort" constraint for slow operations like
    network retries. If the function takes longer than the specified timeout,
    a TimeoutError is raised.

    Args:
        func: The function to wrap.
        timeout: Timeout in seconds. If None, uses PER_OPERATION_TIMEOUT from config.

    Returns:
        Wrapped function that enforces the timeout.
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        # Determine the timeout threshold
        operation_timeout = timeout if timeout is not None else PER_OPERATION_TIMEOUT

        # Define the signal handler
        def handler(signum, frame):
            raise TimeoutError(
                f"Operation '{func.__name__}' exceeded timeout of {operation_timeout}s"
            )

        # Set the signal handler for SIGALRM
        # Note: SIGALRM is only available on Unix-like systems
        if sys.platform.startswith('win'):
            logger.warning(
                "Signal-based timeouts are not supported on Windows. "
                "The timeout_guard decorator will be skipped."
            )
            return func(*args, **kwargs)

        old_handler = signal.signal(signal.SIGALRM, handler)
        # Set the alarm
        signal.alarm(operation_timeout)

        try:
            result = func(*args, **kwargs)
        finally:
            # Cancel the alarm
            signal.alarm(0)
            # Restore the old handler
            signal.signal(signal.SIGALRM, old_handler)

        return result

    return wrapper

@contextmanager
def timeout_context(timeout: Optional[int] = None):
    """
    Context manager to enforce a timeout on a block of code.

    Args:
        timeout: Timeout in seconds. If None, uses PER_OPERATION_TIMEOUT from config.

    Yields:
        None

    Raises:
        TimeoutError: If the block exceeds the timeout.
    """
    operation_timeout = timeout if timeout is not None else PER_OPERATION_TIMEOUT

    if sys.platform.startswith('win'):
        logger.warning(
            "Signal-based timeouts are not supported on Windows. "
            "The timeout_context will be skipped."
        )
        yield
        return

    def handler(signum, frame):
        raise TimeoutError(
            f"Code block exceeded timeout of {operation_timeout}s"
        )

    old_handler = signal.signal(signal.SIGALRM, handler)
    signal.alarm(operation_timeout)

    try:
        yield
    finally:
        signal.alarm(0)
        signal.signal(signal.SIGALRM, old_handler)

def get_memory_usage_mb() -> float:
    """
    Get the current memory usage of the process in MB.

    Returns:
        Memory usage in megabytes.
    """
    if sys.platform.startswith('win'):
        # Windows-specific memory usage (approximate)
        try:
            import psutil
            process = psutil.Process(os.getpid())
            return process.memory_info().rss / (1024 * 1024)
        except ImportError:
            return 0.0
    else:
        # Unix-like systems
        usage = resource.getrusage(resource.RUSAGE_SELF)
        # ru_maxrss is in kilobytes on Linux, but bytes on some other systems
        # Convert to MB
        maxrss = usage.ru_maxrss
        if sys.platform == 'darwin':
            # macOS reports in bytes
            return maxrss / (1024 * 1024)
        else:
            # Linux reports in kilobytes
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
            # Check memory after execution
            if not check_memory_usage(limit_gb):
                raise MemoryLimitError(
                    f"Operation '{func.__name__}' exceeded memory limit of {limit_gb}GB. "
                    f"Current usage: {get_memory_usage_mb():.2f}MB"
                )
            return result
        except MemoryLimitError:
            raise
        except Exception as e:
            # Re-raise other exceptions
            raise
    return wrapper
