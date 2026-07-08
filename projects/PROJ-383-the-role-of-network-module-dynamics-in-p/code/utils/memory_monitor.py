import psutil
import os
from typing import Optional, Dict, Any
from contextlib import contextmanager
import logging
from .logging_config import log_memory_usage

_process = psutil.Process(os.getpid())
_peak_rss_bytes: float = 0.0
_limit_bytes: float = 7 * 1024 * 1024 * 1024  # 7GB default

def get_current_rss_bytes() -> int:
    """Return current RSS memory usage in bytes."""
    return _process.memory_info().rss

def get_peak_rss_bytes() -> float:
    """Return the peak RSS memory usage observed in this process."""
    return _peak_rss_bytes

def reset_peak_rss() -> None:
    """Reset the tracked peak RSS to current value."""
    global _peak_rss_bytes
    _peak_rss_bytes = get_current_rss_bytes()

def check_memory_limit(limit_bytes: Optional[float] = None) -> bool:
    """
    Check if current RSS is within the limit.
    Returns True if within limit, False otherwise.
    """
    limit = limit_bytes if limit_bytes is not None else _limit_bytes
    current = get_current_rss_bytes()
    return current <= limit

def enforce_memory_limit(limit_bytes: Optional[float] = None) -> None:
    """
    Enforce memory limit. Raises MemoryError if exceeded.
    Logs memory usage events before raising.
    """
    limit = limit_bytes if limit_bytes is not None else _limit_bytes
    current = get_current_rss_bytes()
    global _peak_rss_bytes
    
    if current > _peak_rss_bytes:
        _peak_rss_bytes = current

    current_mb = current / (1024 * 1024)
    peak_mb = _peak_rss_bytes / (1024 * 1024)
    limit_mb = limit / (1024 * 1024)

    log_memory_usage(current_mb, peak_mb, limit_mb, "check")

    if current > limit:
        log_memory_usage(current_mb, peak_mb, limit_mb, "exceeded")
        raise MemoryError(
            f"Memory limit exceeded: {current_mb:.1f}MB > {limit_mb:.1f}MB limit."
        )

def get_memory_usage_report(limit_bytes: Optional[float] = None) -> Dict[str, Any]:
    """
    Generate a report of current memory usage.
    """
    limit = limit_bytes if limit_bytes is not None else _limit_bytes
    current = get_current_rss_bytes()
    global _peak_rss_bytes
    if current > _peak_rss_bytes:
        _peak_rss_bytes = current

    return {
        "current_rss_bytes": current,
        "current_rss_mb": current / (1024 * 1024),
        "peak_rss_bytes": _peak_rss_bytes,
        "peak_rss_mb": _peak_rss_bytes / (1024 * 1024),
        "limit_bytes": limit,
        "limit_mb": limit / (1024 * 1024),
        "within_limit": current <= limit,
    }

@contextmanager
def memory_guard(limit_bytes: Optional[float] = None):
    """
    Context manager to monitor memory usage within a block.
    Raises MemoryError if limit is exceeded.
    """
    reset_peak_rss()
    try:
        yield
        enforce_memory_limit(limit_bytes)
    except MemoryError:
        raise
    finally:
        enforce_memory_limit(limit_bytes)

def main():
    """CLI test for memory monitor."""
    from .logging_config import setup_logging
    setup_logging()
    
    print("Testing memory monitor...")
    report = get_memory_usage_report()
    print(f"Current: {report['current_rss_mb']:.1f}MB")
    print(f"Peak: {report['peak_rss_mb']:.1f}MB")
    print(f"Limit: {report['limit_mb']:.1f}MB")
    print(f"Within Limit: {report['within_limit']}")

if __name__ == "__main__":
    main()
