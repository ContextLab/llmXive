import psutil
import sys
import os
from typing import Optional

from utils.config import MAX_MEMORY_GB, MAX_CPU_CORES

class ResourceLimitExceeded(Exception):
    """Exception raised when resource limits are exceeded."""
    pass

def check_ram_usage() -> float:
    """
    Check current RAM usage in GB.
    Returns the percentage of RAM used.
    """
    process = psutil.Process(os.getpid())
    memory_info = process.memory_info()
    memory_gb = memory_info.rss / (1024 ** 3)
    return memory_gb

def check_cpu_usage() -> float:
    """
    Check current CPU usage as a percentage.
    """
    return psutil.cpu_percent(interval=0.1)

def check_resource_limits() -> None:
    """
    Check if current resource usage exceeds limits.
    Raises ResourceLimitExceeded if limits are exceeded.
    """
    current_ram = check_ram_usage()
    current_cpu = check_cpu_usage()
    
    if current_ram > MAX_MEMORY_GB:
        raise ResourceLimitExceeded(
            f"RAM usage {current_ram:.2f}GB exceeds limit of {MAX_MEMORY_GB}GB"
        )
    
    if current_cpu > MAX_CPU_CORES * 100:
        raise ResourceLimitExceeded(
            f"CPU usage {current_cpu:.1f}% exceeds limit of {MAX_CPU_CORES * 100}%"
        )

def monitor_resources(interval: float = 1.0, callback: Optional[callable] = None) -> None:
    """
    Continuously monitor resources and raise exception if limits exceeded.
    """
    while True:
        check_resource_limits()
        if callback:
            callback()
        import time
        time.sleep(interval)
