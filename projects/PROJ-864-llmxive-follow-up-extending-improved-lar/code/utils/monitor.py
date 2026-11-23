import os
import sys
import time
import resource
from datetime import datetime
from typing import Optional, Dict, Any, Generator

def get_ram_usage_gb() -> float:
    """
    Get current RAM usage in GB.
    Uses resource module for POSIX systems.
    """
    usage = resource.getrusage(resource.RUSAGE_SELF)
    # maxrss is in kilobytes on Linux/macOS
    maxrss_kb = usage.ru_maxrss
    return maxrss_kb / (1024 * 1024)  # Convert KB to GB

def get_elapsed_time(start_time: float) -> float:
    """Get elapsed time in seconds since start_time."""
    return time.time() - start_time

def check_ram_threshold(limit_gb: float) -> bool:
    """
    Check if current RAM usage exceeds the threshold.
    Returns True if usage is OVER the limit (violation).
    """
    current = get_ram_usage_gb()
    return current > limit_gb

def get_resource_snapshot() -> Dict[str, Any]:
    """
    Capture a snapshot of current resource usage.
    """
    return {
        "timestamp": datetime.now().isoformat(),
        "ram_gb": get_ram_usage_gb(),
        "elapsed_time": None # Caller should pass start time if needed
    }

def resource_monitor(
    start_time: float,
    limit_gb: float,
    interval_seconds: float = 5.0
) -> Generator[Dict[str, Any], None, None]:
    """
    Generator that yields resource snapshots periodically.
    Raises MemoryError if RAM usage exceeds limit_gb.
    """
    while True:
        snapshot = get_resource_snapshot()
        snapshot["elapsed_time"] = get_elapsed_time(start_time)
        
        if snapshot["ram_gb"] > limit_gb:
            raise MemoryError(
                f"RAM usage {snapshot['ram_gb']:.2f} GB exceeded limit of {limit_gb} GB"
            )
        
        yield snapshot
        time.sleep(interval_seconds)