"""
Memory monitoring utilities.
"""
import gc
import logging
import os
import sys
from pathlib import Path
from typing import Optional, Tuple

def setup_memory_monitoring():
    """
    Setup memory monitoring.
    """
    logging.info("Memory monitoring setup complete.")

def get_memory_usage_bytes() -> int:
    """
    Get current memory usage in bytes.
    """
    try:
        import psutil
        process = psutil.Process(os.getpid())
        return process.memory_info().rss
    except ImportError:
        logging.warning("psutil not installed. Memory monitoring disabled.")
        return 0

def get_memory_usage_gb() -> float:
    """
    Get current memory usage in GB.
    """
    return get_memory_usage_bytes() / (1024 ** 3)

def get_memory_percent() -> float:
    """
    Get memory usage as a percentage of total system memory.
    """
    try:
        import psutil
        process = psutil.Process(os.getpid())
        return process.memory_percent()
    except ImportError:
        return 0.0

def get_memory_stats() -> dict:
    """
    Get memory statistics.
    """
    return {
        "rss_bytes": get_memory_usage_bytes(),
        "rss_gb": get_memory_usage_gb(),
        "percent": get_memory_percent()
    }

def check_memory_thresholds(threshold_gb: float = 5.4) -> bool:
    """
    Check if memory usage exceeds threshold.
    """
    usage_gb = get_memory_usage_gb()
    if usage_gb > threshold_gb:
        logging.warning(f"Memory usage {usage_gb:.2f} GB exceeds threshold {threshold_gb} GB.")
        return True
    return False

def trigger_garbage_collection():
    """
    Trigger garbage collection.
    """
    gc.collect()
    logging.info("Garbage collection triggered.")

def check_memory_checkpoint():
    """
    Check memory at a checkpoint.
    """
    stats = get_memory_stats()
    logging.info(f"Memory checkpoint: {stats}")
    if stats['rss_gb'] > 5.4:
        trigger_garbage_collection()

def monitor_and_maybe_gc(threshold_gb: float = 5.4):
    """
    Monitor memory and trigger GC if needed.
    """
    if check_memory_thresholds(threshold_gb):
        trigger_garbage_collection()

def enforce_memory_limit(limit_gb: float = 6.0):
    """
    Enforce a hard memory limit.
    """
    if get_memory_usage_gb() > limit_gb:
        raise MemoryError(f"Memory limit {limit_gb} GB exceeded.")
