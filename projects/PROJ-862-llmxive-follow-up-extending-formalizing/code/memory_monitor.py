import tracemalloc
import resource
import sys
import json
import os
from typing import Optional, Callable, Any, Dict
from contextlib import contextmanager
import logging

logger = logging.getLogger(__name__)

class MemoryLimitExceeded(Exception):
    """Raised when memory usage exceeds the configured limit."""
    pass

_peak_memory = 0
_limit_mb = 7000.0
_profile_path = "data/processed/memory_profile.json"

def reset_memory_tracker():
    global _peak_memory
    _peak_memory = 0
    if not tracemalloc.is_tracing():
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
    # ru_maxrss is in KB on Linux, convert to MB
    return usage.ru_maxrss / 1024.0

def check_memory_limit(limit_mb: float) -> None:
    """
    Checks if current RSS memory usage exceeds the limit.
    Raises MemoryLimitExceeded if the threshold is breached.
    
    Note: The task specifically requires enforcing "peak RSS ≤ 7GB".
    resource.getrusage returns the max RSS (ru_maxrss) for the process.
    We compare the current max RSS against the limit.
    """
    global _peak_memory
    rss = get_rss_memory_mb()
    
    # Update global peak tracker for logging consistency
    if rss > _peak_memory:
        _peak_memory = rss

    if rss > limit_mb:
        logger.error(f"Memory limit exceeded! Peak RSS: {rss:.2f} MB, Limit: {limit_mb:.2f} MB")
        raise MemoryLimitExceeded(f"Peak RSS usage {rss:.2f} MB exceeded limit {limit_mb:.2f} MB")
    
    logger.debug(f"Memory check passed: Peak RSS {rss:.2f} MB, Limit {limit_mb:.2f} MB")

def enforce_memory_limit(limit_mb: float):
    """Decorator to enforce memory limit on a function."""
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
        "peak_tracemalloc_mb": get_peak_memory_mb(),
        "peak_rss_mb": get_rss_memory_mb()
    }

def save_memory_profile(profile_path: Optional[str] = None):
    """
    Saves the current memory profile to data/processed/memory_profile.json.
    MUST log the peak RSS value even if the limit is not breached.
    """
    snapshot = get_memory_snapshot()
    # Add a timestamp for clarity
    import time
    snapshot["timestamp"] = time.time()
    snapshot["limit_mb"] = _limit_mb
    
    path = profile_path if profile_path else _profile_path
    
    # Ensure directory exists
    profile_dir = os.path.dirname(path)
    if profile_dir and not os.path.exists(profile_dir):
        os.makedirs(profile_dir)
    
    with open(path, 'w') as f:
        json.dump(snapshot, f, indent=2)
    
    logger.info(f"Memory profile saved to {path}: {snapshot}")

@contextmanager
def memory_monitor(limit_mb: float = 7000.0, profile_path: Optional[str] = None):
    """
    Context manager to monitor memory usage.
    
    - Starts tracemalloc.
    - Enforces a hard "peak RSS ≤ 7GB" failure condition.
    - Raises MemoryLimitExceeded if the threshold is breached.
    - ALWAYS logs the peak RSS value to data/processed/memory_profile.json on exit,
      regardless of whether the limit was breached or not.
    """
    global _limit_mb, _profile_path
    if profile_path:
        _profile_path = profile_path
    _limit_mb = limit_mb
    
    reset_memory_tracker()
    
    try:
        yield
    finally:
        # CRITICAL: Must save profile even if an exception occurred or limit was not breached
        try:
            save_memory_profile()
        except Exception as e:
            logger.warning(f"Failed to save memory profile: {e}")
        
        # Check limit after saving profile (or if it failed, the exception will propagate)
        # If we are here, we check the limit. If it's exceeded, we raise.
        check_memory_limit(limit_mb)