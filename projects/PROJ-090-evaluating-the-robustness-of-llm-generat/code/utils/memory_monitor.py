"""
Memory monitoring utilities for the LLM robustness pipeline.

This module provides functions to monitor CPU memory usage and enforce
strict limits (e.g., < 6GB per process) to ensure compatibility with
CPU-only inference environments.
"""
import os
import sys
import logging
import resource
from pathlib import Path
from typing import Optional, Callable, Any
from contextlib import contextmanager

# Configure logger
logger = logging.getLogger(__name__)

# Constants
MEMORY_LIMIT_GB = 6.0
MEMORY_LIMIT_BYTES = MEMORY_LIMIT_GB * 1024**3
WARNING_THRESHOLD_GB = 5.5
WARNING_THRESHOLD_BYTES = WARNING_THRESHOLD_GB * 1024**3

def get_current_memory_mb() -> float:
    """
    Get the current resident set size (RSS) of the current process in MB.
    
    Returns:
        float: Current memory usage in MB.
    """
    # Get memory usage in bytes
    usage = resource.getrusage(resource.RUSAGE_SELF)
    # ru_maxrss is in KB on Linux/macOS, but bytes on some systems.
    # On Linux, it's KB. Let's normalize.
    mem_kb = usage.ru_maxrss
    
    # Check OS to determine unit
    if sys.platform == 'darwin':
        # macOS reports in KB
        mem_bytes = mem_kb * 1024
    elif sys.platform.startswith('linux'):
        # Linux reports in KB
        mem_bytes = mem_kb * 1024
    else:
        # Fallback: assume bytes if unknown, though unlikely for standard platforms
        mem_bytes = mem_kb
        
    return mem_bytes / (1024 * 1024)

def check_memory_limit(limit_gb: float = MEMORY_LIMIT_GB) -> bool:
    """
    Check if the current process memory usage is within the specified limit.
    
    Args:
        limit_gb: Memory limit in GB.
        
    Returns:
        bool: True if within limit, False otherwise.
    """
    current_mb = get_current_memory_mb()
    current_bytes = current_mb * 1024 * 1024
    limit_bytes = limit_gb * 1024**3
    
    if current_bytes > limit_bytes:
        logger.error(f"Memory limit exceeded: {current_mb:.2f} MB > {limit_gb * 1024:.2f} MB")
        return False
    
    if current_bytes > WARNING_THRESHOLD_BYTES:
        logger.warning(f"Memory usage high: {current_mb:.2f} MB approaching limit {limit_gb * 1024:.2f} MB")
        
    logger.debug(f"Current memory usage: {current_mb:.2f} MB / {limit_gb * 1024:.2f} MB")
    return True

@contextmanager
def memory_guard(limit_gb: float = MEMORY_LIMIT_GB, action_on_exceed: Optional[Callable[[], None]] = None):
    """
    Context manager to enforce memory limits during a block of execution.
    
    If memory usage exceeds the limit, it logs an error and optionally calls
    an action function (e.g., to cleanup or raise an exception).
    
    Args:
        limit_gb: Memory limit in GB.
        action_on_exceed: Optional function to call if limit is exceeded.
        
    Raises:
        MemoryError: If limit is exceeded and no action is provided.
    """
    try:
        yield
        # Check memory after execution
        if not check_memory_limit(limit_gb):
            if action_on_exceed:
                action_on_exceed()
            else:
                raise MemoryError(f"Process memory exceeded {limit_gb} GB limit")
    except MemoryError:
        raise
    except Exception as e:
        # Re-raise other exceptions
        raise e

def set_soft_memory_limit(limit_gb: float = MEMORY_LIMIT_GB) -> None:
    """
    Set a soft limit on the process's memory usage using resource limits.
    
    This acts as a hard stop at the OS level if the limit is breached,
    preventing the process from consuming more than the specified amount.
    
    Args:
        limit_gb: Memory limit in GB.
    """
    limit_bytes = int(limit_gb * 1024**3)
    try:
        # Set both soft and hard limits
        resource.setrlimit(resource.RLIMIT_AS, (limit_bytes, limit_bytes))
        logger.info(f"Set memory limit to {limit_gb} GB ({limit_bytes} bytes)")
    except ValueError as e:
        logger.warning(f"Could not set memory limit: {e}. Limit enforcement will rely on Python checks.")
    except Exception as e:
        logger.error(f"Failed to set memory limit: {e}")

def main() -> None:
    """
    CLI entry point for memory monitoring and limit setting.
    
    Usage:
        python code/utils/memory_monitor.py [limit_gb]
    """
    if len(sys.argv) > 1:
        try:
            limit = float(sys.argv[1])
        except ValueError:
            print(f"Error: Invalid limit value '{sys.argv[1]}'. Must be a number.")
            sys.exit(1)
    else:
        limit = MEMORY_LIMIT_GB
        
    print(f"Setting memory limit to {limit} GB...")
    set_soft_memory_limit(limit)
    
    print(f"Current memory usage: {get_current_memory_mb():.2f} MB")
    
    if check_memory_limit(limit):
        print(f"Memory usage is within the {limit} GB limit.")
    else:
        print(f"Memory usage exceeds the {limit} GB limit.")
        sys.exit(1)

if __name__ == "__main__":
    main()
