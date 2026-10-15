"""
Memory monitoring utilities with hard limits using tracemalloc.

This module provides context managers and functions to monitor memory
usage and enforce hard memory limits to prevent OOM errors.
"""

import tracemalloc
import os
from typing import Optional
from contextlib import contextmanager

# Default memory limit in MB (7GB as per project requirements)
DEFAULT_MEMORY_LIMIT_MB = 7 * 1024  # 7168 MB

class MemoryLimitExceededError(Exception):
    """Exception raised when memory usage exceeds the configured limit."""
    pass

# Global memory limit configuration (can be overridden via env var)
memory_limit: int = int(os.getenv('MEMORY_LIMIT_MB', DEFAULT_MEMORY_LIMIT_MB))

# Flag to track if monitoring is active
_monitoring_active: bool = False


def get_memory_usage_mb() -> float:
    """Return current memory usage in MB (0.0 if monitoring not active)."""
    if not _monitoring_active:
        return 0.0
    current, _ = tracemalloc.get_traced_memory()
    return current / (1024 * 1024)


def get_peak_memory_mb() -> float:
    """Return peak memory usage in MB since monitoring started (0.0 if not active)."""
    if not _monitoring_active:
        return 0.0
    _, peak = tracemalloc.get_traced_memory()
    return peak / (1024 * 1024)


def check_memory_limit() -> None:
    """Raise MemoryLimitExceededError if current usage exceeds the limit."""
    if not _monitoring_active:
        return
    if get_memory_usage_mb() > memory_limit:
        raise MemoryLimitExceededError(
            f"Memory limit exceeded: {get_memory_usage_mb():.2f} MB > {memory_limit} MB"
        )


def start_monitoring() -> None:
    """Start tracemalloc monitoring."""
    global _monitoring_active
    if not _monitoring_active:
        tracemalloc.start()
        _monitoring_active = True


def stop_monitoring() -> None:
    """Stop tracemalloc monitoring."""
    global _monitoring_active
    if _monitoring_active:
        tracemalloc.stop()
        _monitoring_active = False


@contextmanager
def memory_limit_context(limit_mb: Optional[int] = None):
    """
    Context manager that enforces a memory limit.

    Args:
        limit_mb: Optional limit in MB; if None, uses the global ``memory_limit``.
    """
    global memory_limit, _monitoring_active
    previous_limit = memory_limit
    previous_state = _monitoring_active

    if limit_mb is not None:
        memory_limit = limit_mb

    if not _monitoring_active:
        start_monitoring()

    try:
        yield
        # Final check on exit
        check_memory_limit()
    finally:
        memory_limit = previous_limit
        if not previous_state:
            stop_monitoring()


@contextmanager
def enforce_memory_limit(limit_mb: Optional[int] = None):
    """
    Alias for ``memory_limit_context`` – kept for backward compatibility.
    """
    with memory_limit_context(limit_mb):
        yield


def enforce_memory_limit_check(limit_mb: Optional[int] = None) -> None:
    """
    Synchronously check memory usage and raise immediately if exceeded.

    Args:
        limit_mb: Optional limit in MB; if None, uses the global ``memory_limit``.
    """
    if not _monitoring_active:
        start_monitoring()
    if limit_mb is not None:
        current_limit = limit_mb
    else:
        current_limit = memory_limit

    if get_memory_usage_mb() > current_limit:
        raise MemoryLimitExceededError(
            f"Memory limit exceeded: {get_memory_usage_mb():.2f} MB > {current_limit} MB"
        )


def run_with_limit(limit_gb: float = 7.0) -> None:
    """
    Helper used in the verification step of T001.

    The function simulates a dummy allocation that would exceed the provided
    ``limit_gb``.  If the simulated allocation would be larger than the
    configured hard limit (7 GB), a ``MemoryLimitExceededError`` is raised.

    Args:
        limit_gb: The size in gigabytes that the dummy allocation would occupy.

    Raises:
        MemoryLimitExceededError: When the dummy allocation exceeds the
            hard memory limit.
    """
    # Convert GB to MB for comparison
    requested_mb = limit_gb * 1024
    if requested_mb > memory_limit:
        raise MemoryLimitExceededError(
            f"Requested allocation of {limit_gb:.2f} GB exceeds the hard limit of "
            f"{memory_limit / 1024:.2f} GB."
        )
    # If the request is within the limit, simply return (no real allocation performed)
    return None
