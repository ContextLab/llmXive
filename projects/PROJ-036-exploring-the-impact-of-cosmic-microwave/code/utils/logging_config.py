"""
Logging and resource monitoring configuration.
"""
import logging
import os
import sys
from pathlib import Path
from typing import Optional
import psutil

# Configure logger
logger = logging.getLogger("cmb_lss_pipeline")
logger.setLevel(logging.INFO)

if not logger.handlers:
    handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)


def get_logger() -> logging.Logger:
    """Get the project logger."""
    return logger


def check_memory_limit(limit_gb: float = 7.0) -> bool:
    """
    Check if current memory usage is below the limit.

    Args:
        limit_gb: Memory limit in GB.

    Returns:
        True if within limit, False otherwise.
    """
    try:
        process = psutil.Process(os.getpid())
        mem_info = process.memory_info()
        current_gb = mem_info.rss / (1024 ** 3)

        if current_gb > limit_gb:
            get_logger().warning(f"Memory usage {current_gb:.2f}GB exceeds limit {limit_gb}GB")
            return False
        return True
    except Exception as e:
        get_logger().warning(f"Could not check memory limit: {e}")
        return True  # Fail open if we can't check


def check_disk_limit(path: Optional[Path] = None, limit_gb: float = 14.0) -> bool:
    """
    Check if disk usage is below the limit.

    Args:
        path: Path to check disk space for (default: current working directory).
        limit_gb: Disk limit in GB.

    Returns:
        True if within limit, False otherwise.
    """
    try:
        if path is None:
            path = Path.cwd()

        usage = psutil.disk_usage(str(path))
        available_gb = usage.free / (1024 ** 3)

        if available_gb < limit_gb:
            get_logger().warning(f"Disk space {available_gb:.2f}GB is below limit {limit_gb}GB")
            return False
        return True
    except Exception as e:
        get_logger().warning(f"Could not check disk limit: {e}")
        return True  # Fail open


def log_resource_snapshot(prefix: str = ""):
    """
    Log current memory and disk usage.

    Args:
        prefix: Prefix for the log message.
    """
    try:
        process = psutil.Process(os.getpid())
        mem_info = process.memory_info()
        mem_gb = mem_info.rss / (1024 ** 3)

        usage = psutil.disk_usage('.')
        disk_gb = usage.free / (1024 ** 3)

        get_logger().debug(f"{prefix} Memory: {mem_gb:.2f}GB, Disk Free: {disk_gb:.2f}GB")
    except Exception as e:
        pass  # Silent failure for debug logging
