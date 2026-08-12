import os
import sys
import time
import resource
from datetime import datetime
from typing import Optional, Dict, Any, Generator

def get_ram_usage_gb() -> float:
    """
    Get the current RAM usage in GB.
    
    Returns:
        float: RAM usage in GB.
    """
    usage = resource.getrusage(resource.RUSAGE_SELF)
    # maxru is in KB on Unix, convert to GB
    return usage.ru_maxrss / (1024 * 1024)

def get_elapsed_time(start_time: float) -> float:
    """
    Get the elapsed time since start_time.
    
    Args:
        start_time: Start time in seconds (from time.time())
        
    Returns:
        float: Elapsed time in seconds.
    """
    return time.time() - start_time

def check_ram_threshold(threshold_gb: float = 6.5) -> bool:
    """
    Check if current RAM usage is below the threshold.
    
    Args:
        threshold_gb: RAM threshold in GB.
        
    Returns:
        bool: True if RAM usage is below threshold, False otherwise.
    """
    current_ram = get_ram_usage_gb()
    return current_ram < threshold_gb

def resource_monitor(start_time: float, threshold_gb: float = 6.5) -> Generator[Dict[str, Any], None, None]:
    """
    Generator that yields resource snapshots at intervals.
    
    Args:
        start_time: Start time for elapsed time calculation.
        threshold_gb: RAM threshold for warnings.
        
    Yields:
        Dict with timestamp, elapsed_time, ram_gb, and warning flag.
    """
    while True:
        ram = get_ram_usage_gb()
        elapsed = get_elapsed_time(start_time)
        warning = ram > threshold_gb
        
        yield {
            "timestamp": datetime.now().isoformat(),
            "elapsed_time": elapsed,
            "ram_gb": ram,
            "warning": warning
        }
        
        time.sleep(10)  # Sample every 10 seconds

def get_resource_snapshot() -> Dict[str, Any]:
    """
    Get a snapshot of current resource usage.
    
    Returns:
        Dict with timestamp, elapsed_time, ram_gb.
    """
    return {
        "timestamp": datetime.now().isoformat(),
        "ram_gb": get_ram_usage_gb()
    }
