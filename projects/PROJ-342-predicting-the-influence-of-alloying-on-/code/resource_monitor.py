import os
import sys
import time
import resource
from contextlib import contextmanager
from typing import Generator, Callable, Any, Optional

class ResourceLimitExceeded(Exception):
    """Exception raised when resource limits are exceeded."""
    pass

def get_current_ram_mb() -> float:
    """
    Get the current RAM usage in MB.
    
    Returns:
        Current RAM usage in MB.
    """
    usage = resource.getrusage(resource.RUSAGE_SELF)
    return usage.ru_maxrss / 1024  # Convert KB to MB on Linux

def get_current_cpu_time() -> float:
    """
    Get the current CPU time in seconds.
    
    Returns:
        Current CPU time in seconds.
    """
    usage = resource.getrusage(resource.RUSAGE_SELF)
    return usage.ru_utime + usage.ru_stime

@contextmanager
def resource_monitor(max_ram_mb: Optional[float] = None, max_cpu_time: Optional[float] = None):
    """
    Context manager to monitor resource usage.
    
    Args:
        max_ram_mb: Maximum RAM usage in MB.
        max_cpu_time: Maximum CPU time in seconds.
        
    Yields:
        None
        
    Raises:
        ResourceLimitExceeded: If limits are exceeded.
    """
    start_time = time.time()
    start_cpu = get_current_cpu_time()
    start_ram = get_current_ram_mb()
    
    try:
        yield
    finally:
        end_time = time.time()
        end_cpu = get_current_cpu_time()
        end_ram = get_current_ram_mb()
        
        elapsed_time = end_time - start_time
        elapsed_cpu = end_cpu - start_cpu
        peak_ram = max(start_ram, end_ram)
        
        print(f"Resource usage:")
        print(f"  Elapsed time: {elapsed_time:.2f}s")
        print(f"  CPU time: {elapsed_cpu:.2f}s")
        print(f"  Peak RAM: {peak_ram:.2f}MB")
        
        if max_ram_mb and peak_ram > max_ram_mb:
            raise ResourceLimitExceeded(f"RAM limit exceeded: {peak_ram:.2f}MB > {max_ram_mb}MB")
        
        if max_cpu_time and elapsed_cpu > max_cpu_time:
            raise ResourceLimitExceeded(f"CPU time limit exceeded: {elapsed_cpu:.2f}s > {max_cpu_time}s")

def enforce_resource_limits(max_ram_mb: float = 7000, max_cpu_time: float = 21600):
    """
    Enforce resource limits by setting soft limits.
    
    Args:
        max_ram_mb: Maximum RAM in MB.
        max_cpu_time: Maximum CPU time in seconds.
    """
    # Set soft limits
    resource.setrlimit(resource.RLIMIT_AS, (max_ram_mb * 1024 * 1024, max_ram_mb * 1024 * 1024))
    resource.setrlimit(resource.RLIMIT_CPU, (max_cpu_time, max_cpu_time))
    
    print(f"Resource limits set: RAM={max_ram_mb}MB, CPU={max_cpu_time}s")

def main():
    """Main function for testing resource monitoring."""
    import time
    
    print("Testing resource monitoring...")
    
    try:
        with resource_monitor(max_ram_mb=10000, max_cpu_time=100):
            time.sleep(1)
            print("Resource monitoring successful")
    except ResourceLimitExceeded as e:
        print(f"Resource limit exceeded: {e}")

if __name__ == "__main__":
    main()