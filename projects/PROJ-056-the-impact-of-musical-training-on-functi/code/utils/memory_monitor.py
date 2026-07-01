"""
Memory monitoring utilities for enforcing RAM limits during data processing.

This module provides functionality to track peak RAM usage and enforce
a maximum memory limit (default 7GB) to prevent system resource exhaustion
during large-scale neuroimaging data processing.
"""

import os
import resource
from typing import Optional

class MemoryLimitExceeded(Exception):
    """Raised when current or peak memory usage exceeds the configured limit."""
    pass


def get_current_memory_mb() -> float:
    """
    Get the current resident set size (RSS) memory usage in megabytes.
    
    Returns:
        float: Current memory usage in MB.
    """
    # Get memory usage in bytes (RSS = Resident Set Size)
    usage = resource.getrusage(resource.RUSAGE_SELF)
    # ru_maxrss is in kilobytes on Linux/macOS
    current_kb = usage.ru_maxrss
    return current_kb / 1024.0


def get_peak_memory_mb() -> float:
    """
    Get the peak resident set size (RSS) memory usage in megabytes since process start.
    
    Returns:
        float: Peak memory usage in MB.
    """
    usage = resource.getrusage(resource.RUSAGE_SELF)
    # ru_maxrss is in kilobytes on Linux/macOS
    peak_kb = usage.ru_maxrss
    return peak_kb / 1024.0


def check_memory_limit(limit_gb: float = 7.0, raise_on_exceed: bool = True) -> bool:
    """
    Check if current memory usage is within the specified limit.
    
    Args:
        limit_gb: Maximum allowed memory usage in gigabytes. Default is 7.0 GB.
        raise_on_exceed: If True, raise MemoryLimitExceeded when limit is exceeded.
                        If False, return False without raising.
    
    Returns:
        bool: True if memory usage is within limit, False otherwise.
    
    Raises:
        MemoryLimitExceeded: If raise_on_exceed is True and memory limit is exceeded.
    """
    current_mb = get_current_memory_mb()
    limit_mb = limit_gb * 1024.0
    
    if current_mb > limit_mb:
        if raise_on_exceed:
            raise MemoryLimitExceeded(
                f"Memory limit exceeded: {current_mb:.2f} MB > {limit_mb:.2f} MB "
                f"({limit_gb} GB)"
            )
        return False
    
    return True


def enforce_memory_limit(limit_gb: float = 7.0) -> None:
    """
    Enforce the memory limit by checking current usage and raising an exception if exceeded.
    
    This is a convenience wrapper around check_memory_limit that always raises
    MemoryLimitExceeded when the limit is breached.
    
    Args:
        limit_gb: Maximum allowed memory usage in gigabytes. Default is 7.0 GB.
    
    Raises:
        MemoryLimitExceeded: If current memory usage exceeds the limit.
    """
    check_memory_limit(limit_gb=limit_gb, raise_on_exceed=True)


def get_memory_usage_report(limit_gb: float = 7.0) -> dict:
    """
    Generate a comprehensive memory usage report.
    
    Args:
        limit_gb: The configured memory limit in gigabytes.
    
    Returns:
        dict: Dictionary containing current_mb, peak_mb, limit_mb, 
              usage_percentage, and status.
    """
    current_mb = get_current_memory_mb()
    peak_mb = get_peak_memory_mb()
    limit_mb = limit_gb * 1024.0
    usage_percentage = (current_mb / limit_mb) * 100 if limit_mb > 0 else 0
    
    status = "OK" if current_mb <= limit_mb else "EXCEEDED"
    
    return {
        "current_mb": current_mb,
        "peak_mb": peak_mb,
        "limit_mb": limit_mb,
        "limit_gb": limit_gb,
        "usage_percentage": usage_percentage,
        "status": status
    }

def simulate_large_memory_usage(size_gb: float) -> None:
    """
    Simulate large memory usage for testing purposes.
    
    This function allocates memory to test the memory monitoring functionality.
    It should only be used in test environments.
    
    Args:
        size_gb: Amount of memory to allocate in gigabytes.
    
    Raises:
        MemoryLimitExceeded: If the allocated memory exceeds the default 7GB limit.
    """
    # Allocate memory as a list of integers
    # Each integer in Python 3 is typically 28 bytes, but we account for list overhead
    bytes_to_allocate = int(size_gb * 1024 * 1024 * 1024)
    # Create a list that will consume approximately the requested memory
    # Using a bytearray is more efficient for raw memory allocation
    large_data = bytearray(bytes_to_allocate)
    
    # Force the memory to be committed by touching it
    large_data[0] = 1
    large_data[-1] = 1
    
    # Check memory after allocation
    enforce_memory_limit()

# Cleanup reference to allow garbage collection in test scenarios
def cleanup_large_memory(data: bytearray) -> None:
    """
    Clean up large memory allocations.
    
    Args:
        data: The bytearray or large data structure to clean up.
    """
    del data
    # Force garbage collection to reclaim memory immediately
    import gc
    gc.collect()
