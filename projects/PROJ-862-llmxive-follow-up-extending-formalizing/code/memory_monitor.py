import tracemalloc
import resource
import sys
import json
import os
from typing import Optional, Callable, Any, Dict
from contextlib import contextmanager
import logging
import time

logger = logging.getLogger(__name__)

class MemoryLimitExceeded(Exception):
    """Raised when memory usage exceeds the configured limit."""
    pass

# Global state for the tracker
_peak_memory = 0.0
_limit_mb = 7000.0
_profile_path = "data/processed/memory_profile.json"
_monitoring_active = False

def reset_memory_tracker():
    """Resets the internal peak memory tracker and starts tracemalloc if needed."""
    global _peak_memory, _monitoring_active
    _peak_memory = 0.0
    _monitoring_active = True
    if not tracemalloc.is_tracing():
        tracemalloc.start()
        logger.info("tracemalloc started for memory monitoring.")

def get_current_memory_mb() -> float:
    """Returns current memory usage in MB (tracemalloc current)."""
    if not _monitoring_active:
        return 0.0
    current, peak = tracemalloc.get_traced_memory()
    return current / (1024 * 1024)

def get_peak_memory_mb() -> float:
    """Returns peak memory usage in MB since tracker start (tracemalloc peak)."""
    if not _monitoring_active:
        return 0.0
    current, peak = tracemalloc.get_traced_memory()
    return peak / (1024 * 1024)

def get_rss_memory_mb() -> float:
    """
    Returns RSS memory usage in MB using resource module.
    ru_maxrss is in KB on Linux, convert to MB.
    """
    try:
        usage = resource.getrusage(resource.RUSAGE_SELF)
        return usage.ru_maxrss / 1024.0
    except Exception:
        # Fallback if resource.getrusage is unavailable (e.g., Windows)
        return 0.0

def check_memory_limit(limit_mb: float = None) -> None:
    """
    Checks if current RSS memory usage exceeds the limit.
    Raises MemoryLimitExceeded if the threshold is breached.
    
    Updates the global peak tracker for logging consistency.
    """
    global _peak_memory
    limit = limit_mb if limit_mb is not None else _limit_mb
    
    rss = get_rss_memory_mb()
    
    # Update global peak tracker for logging consistency
    if rss > _peak_memory:
        _peak_memory = rss
    
    if rss > limit:
        logger.error(f"Memory limit exceeded! Peak RSS: {rss:.2f} MB, Limit: {limit:.2f} MB")
        raise MemoryLimitExceeded(f"Peak RSS usage {rss:.2f} MB exceeded limit {limit:.2f} MB")
    
    logger.debug(f"Memory check passed: Peak RSS {rss:.2f} MB, Limit {limit:.2f} MB")

def enforce_memory_limit(limit_mb: float = None):
    """Decorator to enforce memory limit on a function."""
    limit = limit_mb if limit_mb is not None else _limit_mb
    def decorator(func):
        def wrapper(*args, **kwargs):
            check_memory_limit(limit)
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

def save_memory_profile(profile_path: Optional[str] = None, limit_mb: Optional[float] = None):
    """
    Saves the current memory profile to data/processed/memory_profile.json.
    MUST log the peak RSS value even if the limit is not breached.
    """
    global _limit_mb
    snapshot = get_memory_snapshot()
    # Add a timestamp for clarity
    snapshot["timestamp"] = time.time()
    snapshot["limit_mb"] = limit_mb if limit_mb is not None else _limit_mb
    snapshot["peak_rss_recorded_mb"] = _peak_memory
    
    path = profile_path if profile_path else _profile_path
    
    # Ensure directory exists
    profile_dir = os.path.dirname(path)
    if profile_dir and not os.path.exists(profile_dir):
        os.makedirs(profile_dir, exist_ok=True)
    
    with open(path, 'w') as f:
        json.dump(snapshot, f, indent=2)
    
    logger.info(f"Memory profile saved to {path}: {snapshot}")

@contextmanager
def memory_monitor(limit_mb: float = 7000.0, profile_path: Optional[str] = None):
    """
    Context manager to monitor memory usage for the entire process.
    
    - Starts tracemalloc.
    - Enforces a hard "peak RSS ≤ 7GB" failure condition.
    - Raises MemoryLimitExceeded if the threshold is breached.
    - ALWAYS logs the peak RSS value to data/processed/memory_profile.json on exit,
      regardless of whether the limit was breached or not.
    """
    global _limit_mb, _profile_path, _peak_memory, _monitoring_active
    
    original_limit = _limit_mb
    original_path = _profile_path
    original_peak = _peak_memory
    
    if profile_path:
        _profile_path = profile_path
    _limit_mb = limit_mb
    _peak_memory = 0.0
    _monitoring_active = True
    
    # Start tracemalloc if not already running
    if not tracemalloc.is_tracing():
        tracemalloc.start()
    
    try:
        yield
    finally:
        # CRITICAL: Must save profile even if an exception occurred or limit was not breached
        try:
            # Capture the final RSS before cleanup
            final_rss = get_rss_memory_mb()
            if final_rss > _peak_memory:
                _peak_memory = final_rss
            save_memory_profile(profile_path=_profile_path, limit_mb=_limit_mb)
        except Exception as e:
            logger.warning(f"Failed to save memory profile: {e}")
        
        # Restore original state if needed (optional, but good practice)
        # _limit_mb = original_limit
        # _profile_path = original_path
        
        # Check limit after saving profile. If exceeded, raise.
        # Note: We check the limit here. If the limit was already exceeded during the block,
        # the check_memory_limit call inside the block would have raised.
        # If we are here, it means we finished the block. We check the final state.
        check_memory_limit(_limit_mb)

# Convenience functions for direct usage if context manager is not desired
def start_monitoring(limit_mb: float = 7000.0):
    """Starts global memory monitoring."""
    global _limit_mb, _monitoring_active
    _limit_mb = limit_mb
    _monitoring_active = True
    if not tracemalloc.is_tracing():
        tracemalloc.start()

def stop_monitoring():
    """Stops global memory monitoring and saves profile."""
    global _monitoring_active
    _monitoring_active = False
    if tracemalloc.is_tracing():
        tracemalloc.stop()
    
    # Save final profile
    try:
        save_memory_profile()
    except Exception as e:
        logger.warning(f"Failed to save memory profile on stop: {e}")