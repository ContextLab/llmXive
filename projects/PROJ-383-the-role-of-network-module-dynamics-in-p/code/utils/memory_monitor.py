import psutil
import os
from typing import Optional, Dict, Any
from contextlib import contextmanager

# Memory limit in bytes (7 GB)
MEMORY_LIMIT_BYTES = 7 * 1024**3

_process = psutil.Process(os.getpid())
_peak_rss_bytes: Optional[int] = None

def get_current_rss_bytes() -> int:
    """Return current RSS memory usage in bytes."""
    return _process.memory_info().rss

def get_peak_rss_bytes() -> int:
    """Return the peak RSS memory usage observed so far in bytes."""
    global _peak_rss_bytes
    current = get_current_rss_bytes()
    if _peak_rss_bytes is None or current > _peak_rss_bytes:
        _peak_rss_bytes = current
    return _peak_rss_bytes

def reset_peak_rss() -> None:
    """Reset the tracked peak RSS to the current value."""
    global _peak_rss_bytes
    _peak_rss_bytes = get_current_rss_bytes()

def check_memory_limit(limit_bytes: int = MEMORY_LIMIT_BYTES) -> bool:
    """
    Check if current memory usage is within the limit.
    Returns True if within limit, False otherwise.
    """
    current = get_current_rss_bytes()
    return current <= limit_bytes

def enforce_memory_limit(limit_bytes: int = MEMORY_LIMIT_BYTES) -> None:
    """
    Enforce the memory limit. Raises MemoryError if exceeded.
    """
    current = get_current_rss_bytes()
    if current > limit_bytes:
        raise MemoryError(
            f"Memory limit exceeded: {current / (1024**3):.2f} GB > "
            f"{limit_bytes / (1024**3):.2f} GB"
        )

def get_memory_usage_report() -> Dict[str, Any]:
    """
    Generate a detailed memory usage report.
    Returns a dictionary with current, peak, and limit info.
    """
    current = get_current_rss_bytes()
    peak = get_peak_rss_bytes()
    limit = MEMORY_LIMIT_BYTES
    return {
        "current_rss_bytes": current,
        "current_rss_gb": current / (1024**3),
        "peak_rss_bytes": peak,
        "peak_rss_gb": peak / (1024**3),
        "limit_bytes": limit,
        "limit_gb": limit / (1024**3),
        "within_limit": current <= limit,
    }

@contextmanager
def memory_guard(limit_bytes: int = MEMORY_LIMIT_BYTES):
    """
    Context manager that checks memory usage upon exit.
    Raises MemoryError if the limit is exceeded.
    """
    reset_peak_rss()
    try:
        yield
    finally:
        enforce_memory_limit(limit_bytes)
