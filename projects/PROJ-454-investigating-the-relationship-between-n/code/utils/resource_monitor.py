import os
import sys
import psutil
import logging
from pathlib import Path
from datetime import datetime
from typing import Optional

# Constants for limits (from T004)
RAM_LIMIT_GB = 7.0
DISK_LIMIT_GB = 14.0

def get_memory_usage_gb() -> float:
    """Get current process memory usage in GB."""
    process = psutil.Process(os.getpid())
    mem_info = process.memory_info()
    return mem_info.rss / (1024 ** 3)

def get_disk_usage_gb(path: str = "/") -> float:
    """Get disk usage for the specified path in GB."""
    try:
        usage = psutil.disk_usage(path)
        return usage.used / (1024 ** 3)
    except Exception:
        return 0.0

def check_resource_limits(logger: Optional[logging.Logger] = None) -> bool:
    """
    Check if current resource usage is within limits.
    Returns True if within limits, False otherwise.
    Logs warnings if limits are exceeded.
    """
    ram_usage = get_memory_usage_gb()
    disk_usage = get_disk_usage_gb(str(Path(__file__).parent.parent.parent))

    is_ok = True

    if ram_usage > RAM_LIMIT_GB:
        msg = f"CRITICAL: RAM usage {ram_usage:.2f} GB exceeds limit of {RAM_LIMIT_GB} GB"
        if logger:
            logger.critical(msg)
        else:
            print(msg, file=sys.stderr)
        is_ok = False
    elif ram_usage > RAM_LIMIT_GB * 0.9:
        msg = f"WARNING: RAM usage {ram_usage:.2f} GB is approaching limit of {RAM_LIMIT_GB} GB"
        if logger:
            logger.warning(msg)
        else:
            print(msg)

    if disk_usage > DISK_LIMIT_GB:
        msg = f"CRITICAL: Disk usage {disk_usage:.2f} GB exceeds limit of {DISK_LIMIT_GB} GB"
        if logger:
            logger.critical(msg)
        else:
            print(msg, file=sys.stderr)
        is_ok = False
    elif disk_usage > DISK_LIMIT_GB * 0.9:
        msg = f"WARNING: Disk usage {disk_usage:.2f} GB is approaching limit of {DISK_LIMIT_GB} GB"
        if logger:
            logger.warning(msg)
        else:
            print(msg)

    return is_ok

def log_resource_snapshot(logger: logging.Logger, stage: str = "checkpoint") -> None:
    """Log current resource usage snapshot for a specific stage."""
    ram_usage = get_memory_usage_gb()
    disk_usage = get_disk_usage_gb(str(Path(__file__).parent.parent.parent))
    timestamp = datetime.now().isoformat()
    
    log_msg = f"Resource Snapshot [{stage}]: RAM={ram_usage:.3f} GB, Disk={disk_usage:.3f} GB"
    logger.info(log_msg)

def enforce_resource_limits(logger: Optional[logging.Logger] = None) -> None:
    """
    Enforce resource limits. If limits are exceeded, raise a RuntimeError.
    This should be called at critical points in the pipeline.
    """
    if not check_resource_limits(logger):
        ram_usage = get_memory_usage_gb()
        disk_usage = get_disk_usage_gb(str(Path(__file__).parent.parent.parent))
        raise RuntimeError(
            f"Resource limits exceeded: RAM={ram_usage:.2f} GB (limit={RAM_LIMIT_GB} GB), "
            f"Disk={disk_usage:.2f} GB (limit={DISK_LIMIT_GB} GB)"
        )
