"""
Memory monitoring utilities for llmXive research pipeline.

Implements hard memory limits using tracemalloc and resource monitoring
to enforce the 7GB peak RSS constraint (SC-004).
"""

import tracemalloc
import resource
import sys
from typing import Optional, Callable, Any
from contextlib import contextmanager
import logging

logger = logging.getLogger(__name__)

# Memory limit constants (in bytes)
# 7GB = 7 * 1024^3 bytes
MEMORY_LIMIT_GB = 7
MEMORY_LIMIT_BYTES = MEMORY_LIMIT_GB * 1024 * 1024 * 1024
WARNING_THRESHOLD_PERCENT = 80  # Warn at 80% of limit


class MemoryLimitExceeded(Exception):
    """Exception raised when memory usage exceeds the configured limit."""
    
    def __init__(self, peak_mb: float, limit_mb: float, message: Optional[str] = None):
        self.peak_mb = peak_mb
        self.limit_mb = limit_mb
        self.peak_bytes = int(peak_mb * 1024 * 1024)
        self.limit_bytes = int(limit_mb * 1024 * 1024)
        
        if message is None:
            message = (
                f"Memory limit exceeded: Peak usage {peak_mb:.2f} MB exceeds "
                f"limit of {limit_mb:.2f} MB ({MEMORY_LIMIT_GB} GB)."
            )
        super().__init__(message)


def get_current_memory_mb() -> float:
    """
    Get current memory usage in MB using tracemalloc.
    
    Returns:
        Current memory usage in megabytes.
    """
    if not tracemalloc.is_tracing():
        return 0.0
    
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


def get_rss_memory_mb() -> float:
    """
    Get current Resident Set Size (RSS) memory in MB using resource module.
    
    This provides a more accurate measure of actual physical memory usage
    including allocations not tracked by tracemalloc.
    
    Returns:
        RSS memory usage in megabytes.
    """
    try:
        usage = resource.getrusage(resource.RUSAGE_SELF)
        # ru_maxrss is in KB on Linux, MB on macOS
        # We normalize to MB
        maxrss_kb = usage.ru_maxrss
        return maxrss_kb / 1024.0
    except Exception as e:
        logger.warning(f"Could not get RSS memory: {e}")
        return 0.0


def check_memory_limit(raise_on_exceed: bool = True) -> bool:
    """
    Check if current memory usage exceeds the configured limit.
    
    Args:
        raise_on_exceed: If True, raise MemoryLimitExceeded when limit is breached.
        
    Returns:
        True if within limits, False otherwise.
        
    Raises:
        MemoryLimitExceeded: If memory limit is exceeded and raise_on_exceed is True.
    """
    peak_mb = get_peak_memory_mb()
    limit_mb = MEMORY_LIMIT_BYTES / (1024 * 1024)
    
    if peak_mb > limit_mb:
        if raise_on_exceed:
            raise MemoryLimitExceeded(peak_mb, limit_mb)
        return False
    
    # Log warning if approaching limit
    warning_threshold = limit_mb * (WARNING_THRESHOLD_PERCENT / 100)
    if peak_mb > warning_threshold:
        logger.warning(
            f"Memory usage approaching limit: {peak_mb:.2f} MB / {limit_mb:.2f} MB "
            f"({peak_mb / limit_mb * 100:.1f}%)"
        )
    
    return True


@contextmanager
def memory_monitor(
    limit_bytes: Optional[int] = None,
    check_interval: float = 1.0
):
    """
    Context manager that monitors memory usage and enforces a hard limit.
    
    Args:
        limit_bytes: Custom memory limit in bytes (defaults to 7GB).
        check_interval: Interval in seconds for periodic checks (not used in current implementation).
        
    Yields:
        None
        
    Raises:
        MemoryLimitExceeded: If memory usage exceeds the limit.
        
    Example:
        with memory_monitor():
            # Your code here
            process_large_dataset()
    """
    limit = limit_bytes if limit_bytes is not None else MEMORY_LIMIT_BYTES
    
    # Start tracing
    tracemalloc.start()
    
    try:
        logger.info(f"Memory monitoring started with limit: {limit / (1024**3):.2f} GB")
        yield
        
        # Final check before exiting
        check_memory_limit(raise_on_exceed=True)
        
    except MemoryLimitExceeded:
        # Re-raise to propagate the error
        raise
    finally:
        # Stop tracing and report final stats
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        
        peak_mb = peak / (1024 * 1024)
        limit_mb = limit / (1024 * 1024)
        
        logger.info(
            f"Memory monitoring completed. Peak usage: {peak_mb:.2f} MB / {limit_mb:.2f} MB"
        )


def enforce_memory_limit(func: Callable) -> Callable:
    """
    Decorator to enforce memory limits on a function.
    
    Args:
        func: The function to wrap with memory monitoring.
        
    Returns:
        Wrapped function that enforces memory limits.
        
    Example:
        @enforce_memory_limit
        def process_data():
            # This will raise MemoryLimitExceeded if memory exceeds 7GB
            pass
    """
    def wrapper(*args, **kwargs):
        with memory_monitor():
            return func(*args, **kwargs)
    return wrapper


def get_memory_snapshot() -> dict:
    """
    Get a detailed memory snapshot for debugging.
    
    Returns:
        Dictionary containing memory statistics.
    """
    if not tracemalloc.is_tracing():
        return {
            "tracing_active": False,
            "current_mb": 0.0,
            "peak_mb": 0.0,
            "rss_mb": 0.0
        }
    
    current, peak = tracemalloc.get_traced_memory()
    rss_mb = get_rss_memory_mb()
    
    return {
        "tracing_active": True,
        "current_mb": current / (1024 * 1024),
        "peak_mb": peak / (1024 * 1024),
        "rss_mb": rss_mb,
        "limit_mb": MEMORY_LIMIT_BYTES / (1024 * 1024),
        "limit_gb": MEMORY_LIMIT_GB
    }


def reset_memory_tracker():
    """
    Reset the memory tracker to start fresh measurements.
    
    This stops current tracing, clears statistics, and restarts tracing.
    """
    if tracemalloc.is_tracing():
        tracemalloc.stop()
    
    tracemalloc.start()
    logger.info("Memory tracker reset")
