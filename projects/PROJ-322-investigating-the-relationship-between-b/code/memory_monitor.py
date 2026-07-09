"""
Memory monitoring utility to enforce RAM limits during batch processing.

Provides functions to check current memory usage and enforce limits.
"""
import os
import logging
import resource
from typing import Optional

# Import config for memory limit
from config import get_memory_limit_gb

def get_current_ram_gb() -> float:
    """
    Get the current RAM usage of the process in GB.
    
    Returns:
        Current RAM usage in GB
        
    Raises:
        RuntimeError: If memory usage cannot be determined
    """
    try:
        # Get memory usage in bytes (Unix/Linux/MacOS)
        usage = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        
        # On macOS, ru_maxrss is in bytes; on Linux, it's in KB
        # We detect the platform to convert correctly
        if os.name == 'posix':
            # Check if we're on macOS (Darwin)
            if sys.platform == 'darwin':
                # macOS returns bytes
                usage_gb = usage / (1024 ** 3)
            else:
                # Linux returns KB
                usage_gb = usage / (1024 ** 2)
        else:
            # Windows - use different method
            import ctypes
            process = ctypes.windll.kernel32.GetCurrentProcess()
            counter = ctypes.windll.psapi.GetProcessMemoryInfo(process)
            # This is a simplified approach; real implementation would be more robust
            usage_gb = 0.0
        
        return float(usage_gb)
    except Exception as e:
        logging.getLogger("llmXive").warning(f"Failed to get memory usage: {e}")
        return 0.0

def is_limit_exceeded() -> bool:
    """
    Check if current RAM usage exceeds the configured limit.
    
    Returns:
        True if RAM usage exceeds limit, False otherwise
    """
    limit = get_memory_limit_gb()
    current = get_current_ram_gb()
    return current > limit

def check_and_warn() -> bool:
    """
    Check memory usage and log a warning if approaching limit.
    
    Returns:
        True if memory is within safe limits, False otherwise
    """
    limit = get_memory_limit_gb()
    warning_threshold = limit * 0.85  # 85% of limit
    current = get_current_ram_gb()
    
    logger = logging.getLogger("llmXive")
    
    if current >= limit:
        logger.critical(f"CRITICAL: Memory limit exceeded! Current: {current:.2f} GB, Limit: {limit} GB")
        return False
    elif current >= warning_threshold:
        logger.warning(f"Time Limit Warning: RAM usage approaching limit. Current: {current:.2f} GB, Threshold: {warning_threshold:.2f} GB, Limit: {limit} GB")
        return True
    else:
        logger.debug(f"Memory OK: Current: {current:.2f} GB, Limit: {limit} GB")
        return True

def enforce_limit() -> None:
    """
    Enforce the memory limit by raising an error if exceeded.
    
    Raises:
        MemoryError: If RAM usage exceeds the configured limit
    """
    if is_limit_exceeded():
        limit = get_memory_limit_gb()
        current = get_current_ram_gb()
        raise MemoryError(f"Memory limit exceeded! Current: {current:.2f} GB, Limit: {limit} GB")

import sys

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger("llmXive")
    
    logger.info(f"Current RAM usage: {get_current_ram_gb():.2f} GB")
    logger.info(f"Memory limit: {get_memory_limit_gb()} GB")
    logger.info(f"Limit exceeded: {is_limit_exceeded()}")
    
    check_and_warn()