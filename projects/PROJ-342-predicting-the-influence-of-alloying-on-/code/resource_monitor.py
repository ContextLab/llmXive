"""
Resource monitoring wrapper for enforcing CPU time and RAM limits.

This module provides a context manager and decorator to monitor resource usage
during execution and raise exceptions when limits are exceeded.

Requirements:
- FR-005: Enforce 6h CPU time and 7GB RAM limits
"""
import os
import sys
import time
import resource
import logging
import threading
from contextlib import contextmanager
from typing import Optional, Callable, Any
from functools import wraps

# Configure logger
logger = logging.getLogger(__name__)

class ResourceLimitExceeded(Exception):
    """Exception raised when a resource limit is exceeded."""
    pass


def get_current_ram_mb() -> float:
    """
    Get the current RAM usage of the process in MB.
    
    Returns:
        float: Current RAM usage in MB
    """
    # Get memory info from resource module (works on Unix)
    usage = resource.getrusage(resource.RUSAGE_SELF)
    # ru_maxrss is in KB on Linux, MB on macOS
    if sys.platform == 'darwin':
        return usage.ru_maxrss
    else:
        return usage.ru_maxrss / 1024.0


def get_current_cpu_time() -> float:
    """
    Get the cumulative CPU time used by the process in seconds.
    
    Returns:
        float: CPU time in seconds
    """
    usage = resource.getrusage(resource.RUSAGE_SELF)
    return usage.ru_utime + usage.ru_stime


def _get_env_limit(var_name: str, default_seconds: float, unit_factor: float = 1.0) -> float:
    """
    Helper to read a limit from environment variables, overriding defaults.
    
    Args:
        var_name: Environment variable name (e.g., 'RUNTIME_LIMIT_H')
        default_seconds: Default limit in seconds
        unit_factor: Multiplier for the input unit (e.g., 3600 for hours to seconds)
        
    Returns:
        float: The limit in seconds
    """
    env_val = os.environ.get(var_name)
    if env_val is not None:
        try:
            val = float(env_val)
            # Convert from hours to seconds if the variable implies hours
            if 'H' in var_name or 'HOURS' in var_name:
                return val * 3600.0
            # If it's GB for memory, convert to MB
            if 'GB' in var_name and 'RAM' in var_name:
                return val * 1024.0
            return val * unit_factor
        except ValueError:
            logger.warning(f"Invalid value for {var_name}: {env_val}. Using default.")
    return default_seconds


@contextmanager
def resource_monitor(
    cpu_limit: Optional[float] = None,
    ram_limit: Optional[float] = None,
    check_interval: float = 60.0  # Check every 60 seconds
):
    """
    Context manager to monitor CPU time and RAM usage.
    
    Args:
        cpu_limit: Maximum allowed CPU time in seconds. If None, reads from RUNTIME_LIMIT_H env var, else defaults to 6h.
        ram_limit: Maximum allowed RAM in MB. If None, reads from MEMORY_LIMIT_GB env var, else defaults to 7GB.
        check_interval: Interval between resource checks in seconds (default: 60s)
        
    Yields:
        None
        
    Raises:
        ResourceLimitExceeded: If CPU time or RAM limit is exceeded
    """
    # Determine limits: Env Var -> Argument -> Default
    if cpu_limit is None:
        cpu_limit = _get_env_limit('RUNTIME_LIMIT_H', 6 * 3600)
    
    if ram_limit is None:
        ram_limit = _get_env_limit('MEMORY_LIMIT_GB', 7 * 1024)

    start_time = time.time()
    last_check_time = start_time
    
    # Start monitoring thread
    stop_event = threading.Event()
    monitor_thread = threading.Thread(
        target=_monitor_resources,
        args=(cpu_limit, ram_limit, check_interval, stop_event),
        daemon=True
    )
    monitor_thread.start()
    
    try:
        yield
    except Exception as e:
        raise e
    finally:
        stop_event.set()
        monitor_thread.join(timeout=1.0)
        
        # Final check
        current_cpu = get_current_cpu_time()
        current_ram = get_current_ram_mb()
        
        if current_cpu > cpu_limit:
            raise ResourceLimitExceeded(
                f"CPU time limit exceeded: {current_cpu:.2f}s > {cpu_limit:.2f}s"
            )
        if current_ram > ram_limit:
            raise ResourceLimitExceeded(
                f"RAM limit exceeded: {current_ram:.2f}MB > {ram_limit:.2f}MB"
            )


def _monitor_resources(
    cpu_limit: float,
    ram_limit: float,
    check_interval: float,
    stop_event: threading.Event
):
    """
    Background thread function to monitor resources.
    
    Args:
        cpu_limit: Maximum allowed CPU time in seconds
        ram_limit: Maximum allowed RAM in MB
        check_interval: Interval between checks in seconds
        stop_event: Event to signal thread to stop
    """
    while not stop_event.is_set():
        if stop_event.wait(timeout=check_interval):
            break
            
        current_cpu = get_current_cpu_time()
        current_ram = get_current_ram_mb()
        
        logger.info(
            f"Resource check - CPU: {current_cpu:.2f}s / {cpu_limit:.2f}s, "
            f"RAM: {current_ram:.2f}MB / {ram_limit:.2f}MB"
        )
        
        if current_cpu > cpu_limit:
            logger.error(
                f"CPU time limit exceeded: {current_cpu:.2f}s > {cpu_limit:.2f}s"
            )
            raise ResourceLimitExceeded(
                f"CPU time limit exceeded: {current_cpu:.2f}s > {cpu_limit:.2f}s"
            )
            
        if current_ram > ram_limit:
            logger.error(
                f"RAM limit exceeded: {current_ram:.2f}MB > {ram_limit:.2f}MB"
            )
            raise ResourceLimitExceeded(
                f"RAM limit exceeded: {current_ram:.2f}MB > {ram_limit:.2f}MB"
            )


def enforce_resource_limits(
    cpu_limit: Optional[float] = None,
    ram_limit: Optional[float] = None,
    check_interval: float = 60.0  # Check every 60 seconds
):
    """
    Decorator to enforce resource limits on a function.
    
    Args:
        cpu_limit: Maximum allowed CPU time in seconds. If None, reads from RUNTIME_LIMIT_H env var, else defaults to 6h.
        ram_limit: Maximum allowed RAM in MB. If None, reads from MEMORY_LIMIT_GB env var, else defaults to 7GB.
        check_interval: Interval between resource checks in seconds (default: 60s)
        
    Returns:
        Callable: Wrapped function with resource monitoring
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            with resource_monitor(
                cpu_limit=cpu_limit,
                ram_limit=ram_limit,
                check_interval=check_interval
            ):
                return func(*args, **kwargs)
        return wrapper
    return decorator


def main():
    """
    Demo function to test resource monitoring.
    """
    @enforce_resource_limits(cpu_limit=10, ram_limit=1024)
    def test_function():
        print("Running test function...")
        time.sleep(2)
        return "Success"
    
    try:
        result = test_function()
        print(f"Result: {result}")
    except ResourceLimitExceeded as e:
        print(f"Resource limit exceeded: {e}")


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    main()