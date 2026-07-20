"""
Resource monitoring wrapper to enforce CPU time and RAM limits.
Implements FR-005: Max 6 hours runtime, Max 7GB RAM.
"""
import os
import sys
import time
import resource
from contextlib import contextmanager
from typing import Generator, Callable, Any, Optional

# Constants for limits (FR-005)
MAX_CPU_TIME_SECONDS = 6 * 60 * 60  # 6 hours
MAX_RAM_BYTES = 7 * 1024 * 1024 * 1024  # 7 GB

class ResourceLimitExceeded(Exception):
    """Raised when CPU time or RAM usage exceeds defined limits."""
    pass


def get_current_ram_mb() -> float:
    """
    Get the current resident set size (RSS) of the process in MB.
    
    Returns:
        float: Current RAM usage in MB.
    """
    usage = resource.getrusage(resource.RUSAGE_SELF)
    # ru_maxrss is in KB on Linux/macOS
    return usage.ru_maxrss / 1024.0


def get_current_cpu_time() -> float:
    """
    Get the total CPU time used by the process so far in seconds.
    
    Returns:
        float: Total CPU time in seconds.
    """
    usage = resource.getrusage(resource.RUSAGE_SELF)
    return usage.ru_utime + usage.ru_stime


@contextmanager
def resource_monitor(max_cpu: Optional[float] = None, max_ram: Optional[int] = None):
    """
    Context manager to monitor CPU time and RAM usage during execution.
    
    Args:
        max_cpu: Maximum allowed CPU time in seconds (default: 6 hours).
        max_ram: Maximum allowed RAM in bytes (default: 7 GB).
        
    Yields:
        None
        
    Raises:
        ResourceLimitExceeded: If limits are exceeded during the block.
    """
    if max_cpu is None:
        max_cpu = MAX_CPU_TIME_SECONDS
    if max_ram is None:
        max_ram = MAX_RAM_BYTES

    start_time = time.time()
    
    # Initial RAM check
    initial_ram = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss * 1024
    
    try:
        yield
    finally:
        end_time = time.time()
        elapsed_cpu = get_current_cpu_time()
        current_ram = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss * 1024
        
        # Check CPU time limit
        if elapsed_cpu > max_cpu:
            raise ResourceLimitExceeded(
                f"CPU time limit exceeded: {elapsed_cpu:.2f}s > {max_cpu:.2f}s"
            )
        
        # Check RAM limit
        if current_ram > max_ram:
            raise ResourceLimitExceeded(
                f"RAM limit exceeded: {current_ram / (1024**3):.2f}GB > {max_ram / (1024**3):.2f}GB"
            )


def enforce_resource_limits(func: Callable) -> Callable:
    """
    Decorator to enforce resource limits on a function.
    
    Args:
        func: The function to wrap.
        
    Returns:
        Wrapped function that enforces limits.
    """
    def wrapper(*args, **kwargs) -> Any:
        with resource_monitor():
            return func(*args, **kwargs)
    return wrapper


def main():
    """
    Main entry point for testing the resource monitor.
    Demonstrates monitoring functionality.
    """
    print("Resource Monitor Test")
    print(f"Max CPU Time: {MAX_CPU_TIME_SECONDS / 3600} hours")
    print(f"Max RAM: {MAX_RAM_BYTES / (1024**3)} GB")
    
    # Test current readings
    print(f"Current CPU Time: {get_current_cpu_time():.2f}s")
    print(f"Current RAM: {get_current_ram_mb():.2f} MB")
    
    # Test context manager with a simple operation
    try:
        with resource_monitor():
            # Simulate some work
            total = sum(range(1000000))
            print(f"Computation complete. Sum: {total}")
            print("Resource limits enforced successfully.")
    except ResourceLimitExceeded as e:
        print(f"Resource limit exceeded: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()