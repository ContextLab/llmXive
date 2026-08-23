"""
Memory monitoring utilities with hard limits using tracemalloc.

This module provides context managers and functions to monitor memory
usage and enforce hard memory limits to prevent OOM errors.
"""

import tracemalloc
import os
import sys
from typing import Optional, Callable, Any
from contextlib import contextmanager

# Default memory limit in MB (7GB as per project requirements)
DEFAULT_MEMORY_LIMIT_MB = 7 * 1024  # 7000 MB


class MemoryLimitExceededError(Exception):
    """Exception raised when memory usage exceeds the configured limit."""
    pass


# Global memory limit configuration
memory_limit: int = int(os.getenv('MEMORY_LIMIT_MB', DEFAULT_MEMORY_LIMIT_MB))

# Flag to track if monitoring is active
_monitoring_active: bool = False


def get_memory_usage_mb() -> float:
    """
    Get current memory usage in megabytes.
    
    Returns:
        Current memory usage in MB, or 0.0 if tracemalloc is not running.
    """
    if not _monitoring_active:
        return 0.0
    
    current, _ = tracemalloc.get_traced_memory()
    return current / (1024 * 1024)

def get_peak_memory_mb() -> float:
    """
    Get peak memory usage since monitoring started in megabytes.
    
    Returns:
        Peak memory usage in MB, or 0.0 if tracemalloc is not running.
    """
    if not _monitoring_active:
        return 0.0
    
    _, peak = tracemalloc.get_traced_memory()
    return peak / (1024 * 1024)

def check_memory_limit() -> None:
    """
    Check if current memory usage exceeds the limit.
    
    Raises:
        MemoryLimitExceededError: If memory usage exceeds the configured limit.
    """
    if not _monitoring_active:
        return
    
    current_mb = get_memory_usage_mb()
    if current_mb > memory_limit:
        raise MemoryLimitExceededError(
            f"Memory limit exceeded: {current_mb:.2f} MB > {memory_limit} MB"
        )

def start_monitoring() -> None:
    """Start memory monitoring with tracemalloc."""
    global _monitoring_active
    if not _monitoring_active:
        tracemalloc.start()
        _monitoring_active = True

def stop_monitoring() -> None:
    """Stop memory monitoring and reset state."""
    global _monitoring_active
    if _monitoring_active:
        tracemalloc.stop()
        _monitoring_active = False

@contextmanager
def memory_limit_context(limit_mb: Optional[int] = None):
    """
    Context manager that enforces a memory limit.
    
    Args:
        limit_mb: Optional memory limit in MB. If None, uses the global limit.
    
    Yields:
        None
    
    Raises:
        MemoryLimitExceededError: If memory usage exceeds the limit.
    """
    global _monitoring_active
    old_limit = memory_limit
    old_monitoring = _monitoring_active
    
    if limit_mb is not None:
        memory_limit = limit_mb
    
    if not _monitoring_active:
        start_monitoring()
    
    try:
        yield
        # Final check before exiting context
        check_memory_limit()
    finally:
        memory_limit = old_limit
        if not old_monitoring:
            stop_monitoring()

@contextmanager
def enforce_memory_limit(limit_mb: Optional[int] = None):
    """
    Context manager that periodically checks memory and raises if exceeded.
    
    Args:
        limit_mb: Optional memory limit in MB. If None, uses the global limit.
    
    Raises:
        MemoryLimitExceededError: If memory usage exceeds the limit.
    """
    with memory_limit_context(limit_mb):
        yield

def enforce_memory_limit_check(limit_mb: Optional[int] = None) -> None:
    """
    Synchronously check memory usage and raise immediately if exceeded.
    
    This is the core "memory guard" function required by T015.
    It checks the current memory usage against the specified limit (or global default)
    and raises a MemoryLimitExceededError if the limit is breached.
    
    Args:
        limit_mb: Optional memory limit in MB. If None, uses the global limit.
    
    Raises:
        MemoryLimitExceededError: If memory usage exceeds the limit.
    """
    global _monitoring_active, memory_limit
    
    # Ensure monitoring is active to get accurate readings
    if not _monitoring_active:
        start_monitoring()
    
    # Update limit if provided
    if limit_mb is not None:
        current_limit = limit_mb
    else:
        current_limit = memory_limit
    
    current_mb = get_memory_usage_mb()
    if current_mb > current_limit:
        raise MemoryLimitExceededError(
            f"Memory limit exceeded: {current_mb:.2f} MB > {current_limit} MB"
        )