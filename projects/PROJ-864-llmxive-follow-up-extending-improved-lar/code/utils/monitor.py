"""
Resource monitoring utilities for RAM and time tracking.
"""
import os
import sys
import time
import resource
from datetime import datetime
from typing import Optional, Dict, Any, Generator

def get_ram_usage_gb() -> float:
    """Get current RAM usage in GB."""
    try:
        # Get memory usage in bytes (Linux/macOS)
        usage = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        
        # On macOS, ru_maxrss is in bytes. On Linux, it's in KB.
        if sys.platform == 'darwin':
            return usage / (1024 ** 3)
        else:
            return (usage * 1024) / (1024 ** 3)
    except Exception:
        # Fallback for systems where resource module is limited
        return 0.0

def get_elapsed_time(start_time: float) -> float:
    """Get elapsed time in seconds since start_time."""
    return time.time() - start_time

def check_ram_threshold(threshold_gb: float = 8.0) -> bool:
    """
    Check if current RAM usage exceeds threshold.
    
    Args:
        threshold_gb: RAM threshold in GB
        
    Returns:
        True if usage exceeds threshold, False otherwise
    """
    current_usage = get_ram_usage_gb()
    return current_usage > threshold_gb

def resource_monitor(threshold_gb: float = 8.0) -> Generator[Dict[str, Any], None, None]:
    """
    Generator that yields resource snapshots at regular intervals.
    
    Args:
        threshold_gb: RAM threshold to check against
        
    Yields:
        Dictionary with timestamp, ram_gb, and exceeded flag
    """
    while True:
        ram = get_ram_usage_gb()
        exceeded = ram > threshold_gb
        yield {
            "timestamp": datetime.now().isoformat(),
            "ram_gb": ram,
            "exceeded": exceeded
        }
        time.sleep(10)  # Check every 10 seconds

def get_resource_snapshot() -> Dict[str, Any]:
    """
    Get a snapshot of current resource usage.
    
    Returns:
        Dictionary with current resource metrics
    """
    return {
        "timestamp": datetime.now().isoformat(),
        "ram_gb": get_ram_usage_gb(),
        "cpu_percent": 0.0  # Would need psutil for accurate CPU%
    }
