import os
import sys
import time
import resource
from datetime import datetime
from typing import Optional, Dict, Any, Generator

def get_ram_usage_gb() -> float:
    """
    Get current RAM usage in GB.
    
    Returns:
        RAM usage in GB.
    """
    usage = resource.getrusage(resource.RUSAGE_SELF)
    # maxrss is in KB on Linux/macOS
    return usage.ru_maxrss / (1024 * 1024)

def get_elapsed_time(start_time: float) -> float:
    """
    Get elapsed time since start.
    
    Args:
        start_time: Start time in seconds (time.time()).
    
    Returns:
        Elapsed time in seconds.
    """
    return time.time() - start_time

def check_ram_threshold(threshold_gb: float) -> bool:
    """
    Check if current RAM usage exceeds threshold.
    
    Args:
        threshold_gb: Threshold in GB.
    
    Returns:
        True if usage exceeds threshold.
    """
    return get_ram_usage_gb() > threshold_gb

def get_resource_snapshot() -> Dict[str, Any]:
    """
    Get a snapshot of current resource usage.
    
    Returns:
        Dictionary with RAM, CPU, and timestamp.
    """
    usage = resource.getrusage(resource.RUSAGE_SELF)
    return {
        "timestamp": datetime.now().isoformat(),
        "ram_usage_gb": usage.ru_maxrss / (1024 * 1024),
        "user_time": usage.ru_utime,
        "system_time": usage.ru_stime,
        "max_rss_kb": usage.ru_maxrss
    }

def resource_monitor(threshold_gb: float = 6.5, interval: float = 1.0) -> Generator[Dict[str, Any], None, None]:
    """
    Monitor resource usage periodically.
    
    Args:
        threshold_gb: RAM threshold to watch.
        interval: Check interval in seconds.
    
    Yields:
        Resource snapshots.
    """
    while True:
        snapshot = get_resource_snapshot()
        yield snapshot
        
        if snapshot["ram_usage_gb"] > threshold_gb:
            # Log warning but continue
            pass
        
        time.sleep(interval)