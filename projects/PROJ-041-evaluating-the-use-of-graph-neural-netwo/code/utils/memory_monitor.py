"""
Memory monitoring utilities with hard limits using tracemalloc.

This module provides context managers and functions to monitor memory
usage and enforce hard memory limits to prevent OOM errors.
"""

import os
import tracemalloc
from contextlib import contextmanager
from typing import Callable, Optional, Any

# Default memory limit in MB (7 GB as per project requirements)
DEFAULT_MEMORY_LIMIT_MB = 7 * 1024  # 7168 MB


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
            f"Memory limit exceeded: {get_memory_usage_mb():.2f} MB > {memory_limit} MB"
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
            f"Memory limit exceeded: {get_memory_usage_mb():.2f} MB > {current_limit} MB"
        )


def run_with_limit(limit_gb: float, func: Optional[Callable] = None, *args, **kwargs) -> Any:
    """
    Execute ``func`` under a hard memory limit. If ``func`` is ``None``,
    the function behaves like the original stub and simply checks whether
    the requested allocation (``limit_gb``) would exceed the configured
    limit, raising ``MemoryLimitExceededError`` if so.

    Parameters
    ----------
    limit_gb : float
        Desired memory allocation size in gigabytes.
    func : Callable, optional
        The function to execute under the memory limit. If omitted,
        ``run_with_limit`` only performs the limit‑check.
    *args, **kwargs :
        Arguments forwarded to ``func`` when it is provided.

    Returns
    -------
    Any
        The return value of ``func`` when supplied; otherwise ``None``.

    Raises
    ------
    MemoryLimitExceededError
        If the requested allocation exceeds the hard limit or if the
        monitored memory usage exceeds the limit during ``func`` execution.
    """
    # Convert GB to MB for comparison with the global limit
    requested_mb = limit_gb * 1024

    # If the requested allocation itself exceeds the hard limit, fail fast
    if requested_mb > memory_limit:
        raise MemoryLimitExceededError(
            f"Requested allocation of {limit_gb:.2f} GB exceeds the hard limit of "
            f"{memory_limit / 1024:.2f} GB."
        )

    # No callable supplied – behave like a pure check (backward compatible)
    if func is None:
        return None

    # Execute the callable within the memory‑limit context
    with memory_limit_context(limit_mb=int(requested_mb)):
        result = func(*args, **kwargs)
        # Final check after execution
        check_memory_limit()
        return result


# Backwards‑compatible alias used in older code paths
def run_with_limit_legacy(limit_gb: float) -> None:
    """
    Legacy helper retained for compatibility with older imports.
    It simply proxies to ``run_with_limit`` without a callable.
    """
    run_with_limit(limit_gb)
