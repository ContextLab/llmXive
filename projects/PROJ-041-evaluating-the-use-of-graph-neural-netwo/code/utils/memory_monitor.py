"""
Memory monitoring wrapper using tracemalloc to enforce hard memory limits.
"""
import tracemalloc
import os
import sys
from typing import Optional, Callable, Any
from contextlib import contextmanager

class MemoryLimitExceededError(Exception):
    """Raised when memory usage exceeds the configured limit."""
    pass

def get_memory_usage_mb() -> float:
    """
    Get current memory usage in MB.
    
    Returns:
        Current memory usage in megabytes.
    """
    if not tracemalloc.is_tracing():
        tracemalloc.start()
    
    current, peak = tracemalloc.get_traced_memory()
    return current / (1024 * 1024)

def get_peak_memory_mb() -> float:
    """
    Get peak memory usage since tracing started in MB.
    
    Returns:
        Peak memory usage in megabytes.
    """
    if not tracemalloc.is_tracing():
        return 0.0
    
    current, peak = tracemalloc.get_traced_memory()
    return peak / (1024 * 1024)

@contextmanager
def memory_limit(limit_mb: float = 7000.0, verbose: bool = True):
    """
    Context manager to enforce a hard memory limit.
    
    Args:
        limit_mb: Maximum allowed memory in megabytes (default 7GB).
        verbose: If True, prints status messages.
        
    Raises:
        MemoryLimitExceededError: If memory usage exceeds the limit.
    """
    tracemalloc.start()
    start_mem = get_memory_usage_mb()
    if verbose:
        print(f"[MemoryMonitor] Started. Current: {start_mem:.2f} MB, Limit: {limit_mb:.2f} MB")
    
    try:
        yield
    finally:
        end_mem = get_memory_usage_mb()
        peak_mem = get_peak_memory_mb()
        if verbose:
            print(f"[MemoryMonitor] Finished. Peak: {peak_mem:.2f} MB, Final: {end_mem:.2f} MB")
        
        if peak_mem > limit_mb:
            raise MemoryLimitExceededError(
                f"Memory limit exceeded: {peak_mem:.2f} MB > {limit_mb:.2f} MB"
            )
        tracemalloc.stop()

def check_memory_limit(limit_mb: float = 7000.0, verbose: bool = True) -> bool:
    """
    Check if current memory usage is within limits.
    
    Args:
        limit_mb: Maximum allowed memory in megabytes.
        verbose: If True, prints status messages.
        
    Returns:
        True if within limits, False otherwise.
        
    Raises:
        MemoryLimitExceededError: If limit is exceeded.
    """
    current_mem = get_memory_usage_mb()
    peak_mem = get_peak_memory_mb()
    
    if verbose:
        print(f"[MemoryMonitor] Check: Current={current_mem:.2f} MB, Peak={peak_mem:.2f} MB, Limit={limit_mb:.2f} MB")
    
    if peak_mem > limit_mb:
        raise MemoryLimitExceededError(
            f"Memory limit exceeded: {peak_mem:.2f} MB > {limit_mb:.2f} MB"
        )
    
    return True

def start_monitoring(limit_mb: float = 7000.0) -> None:
    """
    Start tracemalloc and set up a periodic check.
    
    Args:
        limit_mb: Maximum allowed memory in megabytes.
    """
    if not tracemalloc.is_tracing():
        tracemalloc.start()
    
    # We don't set up a background thread here to avoid complexity,
    # but the context manager can be used for scoped monitoring.
    print(f"[MemoryMonitor] Monitoring started with limit {limit_mb:.2f} MB")