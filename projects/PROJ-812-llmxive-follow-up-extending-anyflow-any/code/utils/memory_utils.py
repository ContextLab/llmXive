"""
Memory management utilities for the llmXive pipeline.
Provides functions to clear memory, check usage, and monitor thresholds.
"""
import gc
import os
import sys
import resource
from typing import Optional

from .logging import get_logger

logger = get_logger(__name__)


def clear_memory() -> bool:
    """
    Force garbage collection and clear system memory caches where possible.
    
    This function performs the following steps:
    1. Runs Python's garbage collector multiple times to reclaim unused objects.
    2. On Unix-like systems, attempts to drop OS-level page cache via 
       `gc.collect()` and `resource` limits if available.
    
    Returns:
        bool: True if the operation completed without error, False otherwise.
    """
    try:
        logger.debug("Starting memory cleanup process...")
        
        # Force garbage collection multiple times to ensure deep cleanup
        for i in range(3):
            collected = gc.collect()
            logger.debug(f"GC pass {i+1}: collected {collected} objects")
        
        # On Unix systems, try to drop caches if we have permissions
        # Note: This is best-effort and may require specific permissions
        if sys.platform != 'win32':
            try:
                # Attempt to drop page cache (requires root or specific capabilities)
                # This is a best-effort attempt; failure is logged but not fatal
                os.system("sync; echo 3 > /proc/sys/vm/drop_caches 2>/dev/null || true")
                logger.debug("Attempted to drop OS page caches")
            except Exception as e:
                logger.debug(f"Could not drop OS caches (expected on restricted systems): {e}")
        
        logger.info("Memory cleanup completed successfully")
        return True
    except Exception as e:
        logger.error(f"Error during memory cleanup: {e}")
        return False


def get_memory_usage_mb() -> float:
    """
    Get the current memory usage of the process in megabytes.
    
    Returns:
        float: Memory usage in MB. Returns 0.0 if the operation fails.
    """
    try:
        if sys.platform == 'win32':
            # Windows: use psutil if available, otherwise fallback to 0
            try:
                import psutil
                process = psutil.Process(os.getpid())
                return process.memory_info().rss / (1024 * 1024)
            except ImportError:
                logger.warning("psutil not available on Windows; cannot measure memory usage accurately")
                return 0.0
        else:
            # Unix-like systems: use resource module
            usage = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
            # On Linux, ru_maxrss is in KB; on macOS it's in KB as well
            return usage / 1024.0
    except Exception as e:
        logger.warning(f"Could not measure memory usage: {e}")
        return 0.0


def monitor_memory_threshold(threshold_mb: float) -> bool:
    """
    Check if current memory usage exceeds a specified threshold.
    
    Args:
        threshold_mb: The memory threshold in megabytes.
        
    Returns:
        bool: True if current usage exceeds the threshold, False otherwise.
    """
    current_usage = get_memory_usage_mb()
    
    if current_usage > threshold_mb:
        logger.warning(f"Memory usage {current_usage:.2f} MB exceeds threshold {threshold_mb:.2f} MB")
        return True
    
    logger.debug(f"Memory usage {current_usage:.2f} MB is within threshold {threshold_mb:.2f} MB")
    return False
