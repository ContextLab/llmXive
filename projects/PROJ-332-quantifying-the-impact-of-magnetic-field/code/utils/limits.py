"""
Resource limits and timeout management utilities.

This module provides decorators and context managers for enforcing execution
timeouts and memory limits on functions and code blocks. It uses signal-based
timeout handling and resource usage monitoring to prevent runaway processes.

Functions:
    timeout_guard: Decorator that enforces a maximum execution time.
    timeout_context: Context manager for timeout enforcement within a block.
    get_memory_usage_mb: Get current memory usage in megabytes.
    check_memory_usage: Check if memory usage exceeds a threshold.
    memory_guard: Decorator that enforces a maximum memory limit.

Exceptions:
    TimeoutError: Raised when execution exceeds the specified timeout.
    MemoryLimitError: Raised when memory usage exceeds the specified limit.
"""

import os
import signal
import sys
import resource
from functools import wraps
from contextlib import contextmanager
from typing import Callable, Optional, Any
import logging

logger = logging.getLogger(__name__)


class TimeoutError(Exception):
    """
    Exception raised when a function or code block exceeds its execution timeout.

    Attributes:
        message: Description of the timeout error.
        elapsed_time: Approximate time elapsed before timeout (if available).
    """

    def __init__(self, message: str = "Execution timeout exceeded", elapsed_time: Optional[float] = None):
        self.message = message
        self.elapsed_time = elapsed_time
        super().__init__(self.message)


class MemoryLimitError(Exception):
    """
    Exception raised when memory usage exceeds the specified limit.

    Attributes:
        message: Description of the memory limit error.
        current_usage_mb: Current memory usage in megabytes.
        limit_mb: The configured memory limit in megabytes.
    """

    def __init__(self, message: str = "Memory limit exceeded", current_usage_mb: float = 0.0, limit_mb: float = 0.0):
        self.message = message
        self.current_usage_mb = current_usage_mb
        self.limit_mb = limit_mb
        super().__init__(self.message)


def timeout_guard(seconds: int, error_message: Optional[str] = None) -> Callable:
    """
    Decorator that enforces a maximum execution time on a function.

    This decorator uses signal-based timeout handling to interrupt and abort
    functions that exceed the specified time limit. It is effective for CPU-bound
    operations but has limitations with I/O-bound or blocking operations.

    Args:
        seconds: Maximum allowed execution time in seconds.
        error_message: Optional custom error message. If None, a default message is used.

    Returns:
        A decorated function that will raise TimeoutError if it exceeds the time limit.

    Raises:
        TimeoutError: If the function execution exceeds the specified timeout.
        ValueError: If seconds is not a positive integer.

    Example:
        >>> @timeout_guard(10)
        ... def long_running_task():
        ...     time.sleep(15)
        >>> try:
        ...     long_running_task()
        ... except TimeoutError as e:
        ...     print(f"Task timed out: {e}")
    """
    if seconds <= 0:
        raise ValueError("Timeout duration must be a positive integer.")

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            # Set up the signal handler
            def timeout_handler(signum, frame):
                raise TimeoutError(
                    error_message or f"Function '{func.__name__}' exceeded timeout of {seconds} seconds"
                )

            # Store the old handler
            old_handler = signal.signal(signal.SIGALRM, timeout_handler)

            try:
                # Set the alarm
                signal.alarm(seconds)
                result = func(*args, **kwargs)
                return result
            finally:
                # Cancel the alarm and restore the old handler
                signal.alarm(0)
                signal.signal(signal.SIGALRM, old_handler)

        return wrapper

    return decorator


@contextmanager
def timeout_context(seconds: int, error_message: Optional[str] = None):
    """
    Context manager for enforcing a timeout on a code block.

    This context manager uses signal-based timeout handling to interrupt
    code blocks that exceed the specified time limit.

    Args:
        seconds: Maximum allowed execution time in seconds.
        error_message: Optional custom error message. If None, a default message is used.

    Yields:
        None

    Raises:
        TimeoutError: If the code block execution exceeds the specified timeout.

    Example:
        >>> with timeout_context(10):
        ...     # This code block must complete within 10 seconds
        ...     perform_long_operation()
    """
    if seconds <= 0:
        raise ValueError("Timeout duration must be a positive integer.")

    def timeout_handler(signum, frame):
        raise TimeoutError(
            error_message or f"Code block exceeded timeout of {seconds} seconds"
        )

    old_handler = signal.signal(signal.SIGALRM, timeout_handler)

    try:
        signal.alarm(seconds)
        yield
    finally:
        signal.alarm(0)
        signal.signal(signal.SIGALRM, old_handler)


def get_memory_usage_mb() -> float:
    """
    Get the current memory usage of the process in megabytes.

    This function uses the `resource` module to retrieve the maximum resident
    set size (RSS) of the current process.

    Returns:
        Current memory usage in megabytes.

    Note:
        On some platforms, this may return the peak memory usage rather than
        the current usage.
    """
    usage = resource.getrusage(resource.RUSAGE_SELF)
    # ru_maxrss is in kilobytes on Linux, but bytes on some other platforms
    # We assume Linux/Unix behavior (kilobytes)
    maxrss_kb = usage.ru_maxrss
    return maxrss_kb / 1024.0


def check_memory_usage(limit_mb: float) -> bool:
    """
    Check if the current memory usage is below a specified limit.

    Args:
        limit_mb: Memory limit in megabytes.

    Returns:
        True if current usage is below the limit, False otherwise.

    Example:
        >>> if check_memory_usage(4096):
        ...     print("Memory usage is acceptable")
        ... else:
        ...     print("Memory usage too high")
    """
    current_usage = get_memory_usage_mb()
    return current_usage < limit_mb


def memory_guard(limit_mb: float, error_message: Optional[str] = None) -> Callable:
    """
    Decorator that enforces a maximum memory limit on a function.

    This decorator periodically checks memory usage during function execution
    and raises a MemoryLimitError if the limit is exceeded.

    Note:
        This is a best-effort check and may not catch rapid memory spikes
        between checks. For strict memory limits, consider using cgroups
        or similar OS-level controls.

    Args:
        limit_mb: Maximum allowed memory usage in megabytes.
        error_message: Optional custom error message. If None, a default message is used.

    Returns:
        A decorated function that will raise MemoryLimitError if it exceeds the limit.

    Raises:
        MemoryLimitError: If memory usage exceeds the specified limit.
        ValueError: If limit_mb is not a positive number.

    Example:
        >>> @memory_guard(2048)
        ... def memory_intensive_task():
        ...     data = [0] * 10000000
        ...     return sum(data)
    """
    if limit_mb <= 0:
        raise ValueError("Memory limit must be a positive number.")

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            # Check memory before execution
            if not check_memory_usage(limit_mb):
                current_usage = get_memory_usage_mb()
                raise MemoryLimitError(
                    error_message or f"Memory usage ({current_usage:.2f} MB) exceeds limit ({limit_mb} MB) before execution",
                    current_usage_mb=current_usage,
                    limit_mb=limit_mb
                )

            try:
                result = func(*args, **kwargs)
                # Check memory after execution
                if not check_memory_usage(limit_mb):
                    current_usage = get_memory_usage_mb()
                    raise MemoryLimitError(
                        error_message or f"Memory usage ({current_usage:.2f} MB) exceeds limit ({limit_mb} MB) after execution",
                        current_usage_mb=current_usage,
                        limit_mb=limit_mb
                    )
                return result
            except MemoryLimitError:
                raise
            except Exception as e:
                # Check memory even if an exception occurred
                current_usage = get_memory_usage_mb()
                if current_usage > limit_mb:
                    logger.warning(f"Memory usage ({current_usage:.2f} MB) exceeded limit ({limit_mb} MB) during error handling")
                raise

        return wrapper

    return decorator
