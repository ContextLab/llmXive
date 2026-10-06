"""
Resource Monitoring Utilities.
Implements T004 and supports T017.
"""
import os
import sys
import psutil
import logging
from pathlib import Path
from datetime import datetime
from typing import Optional

# Constants
RAM_LIMIT_GB = 7.0
DISK_LIMIT_GB = 14.0

def get_memory_usage_gb() -> float:
    """Get current process memory usage in GB."""
    process = psutil.Process(os.getpid())
    mem_info = process.memory_info()
    return mem_info.rss / (1024 ** 3)

def get_disk_usage_gb(path: Optional[str] = None) -> float:
    """Get disk usage for the project root or specified path in GB."""
    if path is None:
        path = os.getcwd()
    usage = psutil.disk_usage(path)
    return usage.used / (1024 ** 3)

def check_resource_limits(ram_limit: float = RAM_LIMIT_GB, disk_limit: float = DISK_LIMIT_GB) -> bool:
    """
    Check if current resource usage exceeds limits.
    Returns True if within limits, False if exceeded.
    """
    current_ram = get_memory_usage_gb()
    current_disk = get_disk_usage_gb()
    
    if current_ram > ram_limit:
        raise MemoryError(f"RAM usage {current_ram:.2f}GB exceeds limit {ram_limit}GB")
    if current_disk > disk_limit:
        raise MemoryError(f"Disk usage {current_disk:.2f}GB exceeds limit {disk_limit}GB")
    
    return True

def log_resource_snapshot(logger: logging.Logger, stage: str):
    """Log a snapshot of resource usage at a specific stage."""
    ram = get_memory_usage_gb()
    disk = get_disk_usage_gb()
    timestamp = datetime.now().isoformat()
    
    log_entry = {
        "timestamp": timestamp,
        "stage": stage,
        "ram_gb": round(ram, 3),
        "disk_gb": round(disk, 3)
    }
    
    logger.info(f"Resource Snapshot [{stage}]: RAM={log_entry['ram_gb']}GB, Disk={log_entry['disk_gb']}GB")
    
    # Append to log file
    log_file = Path("logs/resource_usage.log")
    log_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(log_file, 'a') as f:
        f.write(f"{timestamp}|{stage}|{ram:.3f}|{disk:.3f}\n")

def log_resource_usage(logger: logging.Logger, operation: str, ram_gb: Optional[float] = None):
    """Log resource usage for a specific operation."""
    current_ram = ram_gb if ram_gb is not None else get_memory_usage_gb()
    timestamp = datetime.now().isoformat()
    
    # Log to logger
    logger.debug(f"Resource Usage [{operation}]: RAM={current_ram:.3f}GB")
    
    # Append to log file (T017 requirement)
    log_file = Path("logs/resource_usage.log")
    log_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(log_file, 'a') as f:
        f.write(f"{timestamp}|{operation}|{current_ram:.3f}|NA\n")

def enforce_resource_limits():
    """
    Forceful check. If limits are exceeded, raise an exception immediately.
    """
    check_resource_limits()
