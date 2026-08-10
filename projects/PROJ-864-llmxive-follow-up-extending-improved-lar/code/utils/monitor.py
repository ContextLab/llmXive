"""
Resource monitoring utilities for RAM and execution time.
"""
import os
import sys
import time
import resource
from datetime import datetime
from typing import Optional, Dict, Any, Generator

from utils.logging import get_logger, info, warning

logger = get_logger(__name__)

def get_ram_usage_gb() -> float:
    """
    Returns the current RAM usage of the process in GB.
    Uses resource module (Unix-like) or fallback for Windows.
    """
    if sys.platform == 'win32':
        # Fallback for Windows (approximate)
        try:
            import psutil
            process = psutil.Process(os.getpid())
            return process.memory_info().rss / (1024 ** 3)
        except ImportError:
            return 0.0
    else:
        # Unix/Linux/Mac
        usage = resource.getrusage(resource.RUSAGE_SELF)
        # ru_maxrss is in kilobytes on Linux/macOS
        return usage.ru_maxrss / (1024 * 1024) # Convert KB to GB

def get_elapsed_time(start_time: float) -> float:
    """Returns elapsed time in seconds."""
    return time.time() - start_time

def check_ram_threshold(current_ram_gb: float, threshold_gb: float) -> bool:
    """
    Checks if current RAM usage exceeds the threshold.
    
    Args:
        current_ram_gb: Current RAM usage in GB.
        threshold_gb: Threshold in GB.
    
    Returns:
        True if threshold is exceeded, False otherwise.
    """
    return current_ram_gb > threshold_gb

def resource_monitor(
    interval: float = 5.0,
    threshold_gb: Optional[float] = None
) -> Generator[Dict[str, Any], None, None]:
    """
    Generator that yields resource snapshots at intervals.
    
    Args:
        interval: Seconds between snapshots.
        threshold_gb: Optional threshold to log warnings.
    
    Yields:
        Dict with 'timestamp', 'ram_gb', 'elapsed_time'.
    """
    start_time = time.time()
    while True:
        ram = get_ram_usage_gb()
        elapsed = get_elapsed_time(start_time)
        snapshot = {
            "timestamp": datetime.now().isoformat(),
            "ram_gb": round(ram, 3),
            "elapsed_time": round(elapsed, 2)
        }
        
        if threshold_gb and check_ram_threshold(ram, threshold_gb):
            warning(f"RAM usage {ram:.2f}GB exceeds threshold {threshold_gb}GB")
        
        yield snapshot
        time.sleep(interval)

def get_resource_snapshot() -> Dict[str, Any]:
    """
    Returns a single snapshot of current resource usage.
    """
    return {
        "timestamp": datetime.now().isoformat(),
        "ram_gb": round(get_ram_usage_gb(), 3),
        "elapsed_time": 0.0 # Relative to call, not useful here without start time
    }
