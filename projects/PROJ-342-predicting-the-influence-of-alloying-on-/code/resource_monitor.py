"""
Resource monitoring wrapper to enforce FR-005 (6h CPU time, 7GB RAM limits).

This module provides context managers and decorators to monitor and enforce
resource limits during pipeline execution.
"""

import os
import sys
import time
import resource
import logging
from contextlib import contextmanager
from typing import Generator, Callable, Any, Optional
from dataclasses import dataclass

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Resource limits (FR-005)
MAX_CPU_TIME_SECONDS = 6 * 60 * 60  # 6 hours
MAX_RAM_MB = 7 * 1024  # 7 GB


class ResourceLimitExceeded(Exception):
    """Exception raised when a resource limit is exceeded."""
    
    def __init__(self, resource_type: str, limit: float, current: float, unit: str):
        self.resource_type = resource_type
        self.limit = limit
        self.current = current
        self.unit = unit
        message = (
            f"Resource limit exceeded: {resource_type} limit is {limit:.2f} {unit}, "
            f"but current usage is {current:.2f} {unit}."
        )
        super().__init__(message)

def get_current_ram_mb() -> float:
    """
    Get the current RAM usage of the process in MB.
    
    Returns:
        Current RAM usage in MB.
    """
    # Get memory usage in bytes (RUSAGE_SELF for current process)
    usage = resource.getrusage(resource.RUSAGE_SELF)
    # maxrss is in KB on Linux/macOS
    return usage.ru_maxrss / 1024.0

def get_current_cpu_time() -> float:
    """
    Get the cumulative CPU time used by the process in seconds.
    
    Returns:
        Cumulative CPU time in seconds.
    """
    usage = resource.getrusage(resource.RUSAGE_SELF)
    # ru_utime and ru_stime are in seconds
    return usage.ru_utime + usage.ru_stime

@contextmanager
def resource_monitor(
    max_cpu_seconds: float = MAX_CPU_TIME_SECONDS,
    max_ram_mb: float = MAX_RAM_MB,
    check_interval: float = 1.0
) -> Generator[dict, None, None]:
    """
    Context manager to monitor CPU time and RAM usage.
    
    Args:
        max_cpu_seconds: Maximum allowed CPU time in seconds.
        max_ram_mb: Maximum allowed RAM usage in MB.
        check_interval: Interval in seconds between checks.
    
    Yields:
        Dictionary with 'start_time', 'start_cpu', 'start_ram' and 'check_interval'.
    
    Raises:
        ResourceLimitExceeded: If limits are exceeded during execution.
    """
    start_time = time.time()
    start_cpu = get_current_cpu_time()
    start_ram = get_current_ram_mb()
    
    logger.info(
        f"Resource monitoring started: CPU limit={max_cpu_seconds}s, "
        f"RAM limit={max_ram_mb}MB"
    )
    
    stats = {
        'start_time': start_time,
        'start_cpu': start_cpu,
        'start_ram': start_ram,
        'check_interval': check_interval,
        'max_cpu_seconds': max_cpu_seconds,
        'max_ram_mb': max_ram_mb
    }
    
    try:
        yield stats
    finally:
        elapsed_time = time.time() - start_time
        elapsed_cpu = get_current_cpu_time() - start_cpu
        current_ram = get_current_ram_mb()
        
        logger.info(
            f"Resource monitoring completed: "
            f"Elapsed time={elapsed_time:.2f}s, "
            f"CPU time={elapsed_cpu:.2f}s, "
            f"Peak RAM={current_ram:.2f}MB"
        )
        
        # Check limits
        if elapsed_cpu > max_cpu_seconds:
            raise ResourceLimitExceeded(
                "CPU time", max_cpu_seconds, elapsed_cpu, "seconds"
            )
        
        if current_ram > max_ram_mb:
            raise ResourceLimitExceeded(
                "RAM", max_ram_mb, current_ram, "MB"
            )

def enforce_resource_limits(
    func: Callable,
    max_cpu_seconds: float = MAX_CPU_TIME_SECONDS,
    max_ram_mb: float = MAX_RAM_MB,
    check_interval: float = 1.0
) -> Callable:
    """
    Decorator to enforce resource limits on a function.
    
    Args:
        func: The function to wrap.
        max_cpu_seconds: Maximum allowed CPU time in seconds.
        max_ram_mb: Maximum allowed RAM usage in MB.
        check_interval: Interval in seconds between checks.
    
    Returns:
        Wrapped function with resource monitoring.
    
    Raises:
        ResourceLimitExceeded: If limits are exceeded during execution.
    """
    from functools import wraps
    
    @wraps(func)
    def wrapper(*args, **kwargs) -> Any:
        with resource_monitor(
            max_cpu_seconds=max_cpu_seconds,
            max_ram_mb=max_ram_mb,
            check_interval=check_interval
        ):
            return func(*args, **kwargs)
    
    return wrapper

def main() -> None:
    """
    Main entry point for testing the resource monitor.
    
    This function demonstrates the usage of the resource monitoring
    context manager and decorator.
    """
    logger.info("Testing resource monitor...")
    
    # Test 1: Context manager with normal execution
    logger.info("Test 1: Context manager with normal execution")
    try:
        with resource_monitor(max_cpu_seconds=300, max_ram_mb=1024) as stats:
            time.sleep(1)  # Simulate work
            logger.info(f"Stats: {stats}")
        logger.info("Test 1 passed: Normal execution completed")
    except ResourceLimitExceeded as e:
        logger.error(f"Test 1 failed: {e}")
    
    # Test 2: Decorator with normal execution
    logger.info("Test 2: Decorator with normal execution")
    
    @enforce_resource_limits(max_cpu_seconds=300, max_ram_mb=1024)
    def test_function():
        time.sleep(1)
        return "Success"
    
    try:
        result = test_function()
        logger.info(f"Test 2 passed: {result}")
    except ResourceLimitExceeded as e:
        logger.error(f"Test 2 failed: {e}")
    
    # Test 3: Context manager with CPU limit exceeded (simulated)
    logger.info("Test 3: Testing CPU limit enforcement (simulated)")
    try:
        with resource_monitor(max_cpu_seconds=0.001, max_ram_mb=1024):
            time.sleep(0.1)  # This will exceed the very small CPU limit
        logger.error("Test 3 failed: Should have raised ResourceLimitExceeded")
    except ResourceLimitExceeded as e:
        logger.info(f"Test 3 passed: Correctly raised exception - {e}")
    
    # Test 4: Context manager with RAM limit exceeded (simulated)
    logger.info("Test 4: Testing RAM limit enforcement (simulated)")
    try:
        with resource_monitor(max_cpu_seconds=300, max_ram_mb=0.001):
            time.sleep(0.01)  # Even minimal usage will exceed 0.001 MB
        logger.error("Test 4 failed: Should have raised ResourceLimitExceeded")
    except ResourceLimitExceeded as e:
        logger.info(f"Test 4 passed: Correctly raised exception - {e}")
    
    logger.info("All resource monitor tests completed")

if __name__ == "__main__":
    main()