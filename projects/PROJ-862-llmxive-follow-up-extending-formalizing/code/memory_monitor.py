import tracemalloc
import resource
import sys
from typing import Optional, Callable, Any
from contextlib import contextmanager
import logging

logger = logging.getLogger(__name__)

class MemoryLimitExceeded(Exception):
    """Raised when memory usage exceeds the configured limit."""
    pass

_peak_memory = 0
_limit_mb = 7000.0

def reset_memory_tracker():
    global _peak_memory
    _peak_memory = 0
    tracemalloc.start()

def get_current_memory_mb() -> float:
    """Returns current memory usage in MB."""
    current, peak = tracemalloc.get_traced_memory()
    return current / (1024 * 1024)

def get_peak_memory_mb() -> float:
    """Returns peak memory usage in MB since tracker start."""
    current, peak = tracemalloc.get_traced_memory()
    return peak / (1024 * 1024)

def get_rss_memory_mb() -> float:
    """Returns RSS memory usage in MB using resource module."""
    usage = resource.getrusage(resource.RUSAGE_SELF)
    return usage.ru_maxrss / 1024  # KB to MB on Linux

def check_memory_limit(limit_mb: float) -> None:
    """Checks if current memory usage exceeds the limit."""
    global _peak_memory
    current = get_current_memory_mb()
    peak = get_peak_memory_mb()
    
    if peak > limit_mb:
        logger.error(f"Memory limit exceeded! Peak: {peak:.2f} MB, Limit: {limit_mb:.2f} MB")
        raise MemoryLimitExceeded(f"Peak memory usage {peak:.2f} MB exceeded limit {limit_mb:.2f} MB")
    
    logger.debug(f"Memory check passed: Current {current:.2f} MB, Peak {peak:.2f} MB")

def enforce_memory_limit(limit_mb: float):
    """Decorator or wrapper to enforce memory limit."""
    def decorator(func):
        def wrapper(*args, **kwargs):
            check_memory_limit(limit_mb)
            return func(*args, **kwargs)
        return wrapper
    return decorator

def get_memory_snapshot() -> Dict[str, float]:
    """Returns a snapshot of memory metrics."""
    return {
        "current_mb": get_current_memory_mb(),
        "peak_mb": get_peak_memory_mb(),
        "rss_mb": get_rss_memory_mb()
    }

@contextmanager
def memory_monitor(limit_mb: float = 7000.0):
    """Context manager to monitor memory usage."""
    global _limit_mb
    _limit_mb = limit_mb
    reset_memory_tracker()
    try:
        yield
    finally:
        check_memory_limit(limit_mb)
