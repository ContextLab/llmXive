"""
Memory monitoring utility for the llmXive pipeline.
Tracks Resident Set Size (RSS) via /proc/self/status and raises exceptions
if memory usage exceeds the configured threshold (default 7GB).
"""
import os
import time
from typing import Optional, Callable, Any
from pathlib import Path

# Default threshold in bytes (7 GB)
DEFAULT_MEMORY_THRESHOLD_BYTES = 7 * 1024**3

def get_current_rss_bytes() -> int:
    """
    Reads the current Resident Set Size (RSS) of the running process
    from /proc/self/status.
    
    Returns:
        int: RSS in bytes.
    
    Raises:
        RuntimeError: If /proc/self/status is not accessible or malformed.
    """
    try:
        status_path = Path("/proc/self/status")
        if not status_path.exists():
            # Fallback for non-Linux environments (e.g., macOS/Windows)
            # While the task specifies /proc, we provide a safe fallback or raise
            # depending on strictness. Given the constraint "track RSS via /proc/self/status",
            # we assume Linux environment. If not, we raise a clear error.
            raise RuntimeError("Memory monitoring via /proc/self/status is only supported on Linux.")
        
        content = status_path.read_text()
        for line in content.splitlines():
            if line.startswith("VmRSS:"):
                # Format: "VmRSS:     12345 kB"
                parts = line.split()
                if len(parts) >= 2:
                    value_str = parts[1]
                    unit = parts[2]
                    value = int(value_str)
                    if unit == "kB":
                        return value * 1024
                    elif unit == "MB":
                        return value * 1024 * 1024
                    elif unit == "bytes":
                        return value
                    else:
                        raise RuntimeError(f"Unexpected memory unit: {unit}")
        raise RuntimeError("VmRSS line not found in /proc/self/status")
    except FileNotFoundError:
        raise RuntimeError("Could not access /proc/self/status. Memory monitoring is unavailable.")
    except (ValueError, IndexError) as e:
        raise RuntimeError(f"Failed to parse memory status: {e}")

def check_memory_limit(threshold_bytes: Optional[int] = None) -> None:
    """
    Checks if the current process memory usage exceeds the threshold.
    
    Args:
        threshold_bytes: Memory limit in bytes. Defaults to 7GB.
        
    Raises:
        MemoryError: If current RSS exceeds the threshold.
    """
    if threshold_bytes is None:
        threshold_bytes = DEFAULT_MEMORY_THRESHOLD_BYTES
    
    current_rss = get_current_rss_bytes()
    
    if current_rss > threshold_bytes:
        raise MemoryError(
            f"Memory limit exceeded: Current RSS is {current_rss / (1024**3):.2f} GB, "
            f"limit is {threshold_bytes / (1024**3):.2f} GB."
        )

class MemoryMonitor:
    """
    A context manager and decorator for monitoring memory usage.
    """
    
    def __init__(self, threshold_bytes: Optional[int] = None, check_interval: float = 0.1):
        """
        Initializes the memory monitor.
        
        Args:
            threshold_bytes: Maximum allowed memory in bytes.
            check_interval: Time in seconds between checks when used as a context manager.
        """
        self.threshold_bytes = threshold_bytes or DEFAULT_MEMORY_THRESHOLD_BYTES
        self.check_interval = check_interval
        self._monitoring = False
    
    def __enter__(self) -> 'MemoryMonitor':
        self._monitoring = True
        self._start_time = time.time()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self._monitoring = False
        if exc_type is not None:
            # If an exception occurred (e.g., MemoryError), we let it propagate
            pass
    
    def check(self) -> None:
        """Perform a single memory check."""
        check_memory_limit(self.threshold_bytes)
    
    def monitor_loop(self) -> None:
        """
        Continuously checks memory usage in a loop until the context is exited.
        Should be run in a background thread if used alongside main processing.
        """
        while self._monitoring:
            try:
                check_memory_limit(self.threshold_bytes)
            except MemoryError as e:
                self._monitoring = False
                raise
            time.sleep(self.check_interval)

def memory_limit_decorator(threshold_bytes: Optional[int] = None):
    """
    Decorator to enforce memory limits on a function.
    Checks memory before and periodically during execution if the function is long-running.
    Note: For standard functions, this only checks before and after.
    For continuous monitoring, use the MemoryMonitor context manager.
    """
    def decorator(func: Callable) -> Callable:
        def wrapper(*args, **kwargs) -> Any:
            check_memory_limit(threshold_bytes)
            result = func(*args, **kwargs)
            check_memory_limit(threshold_bytes)
            return result
        return wrapper
    return decorator

# Convenience function to raise immediately if over limit
def enforce_memory_limit(threshold_bytes: Optional[int] = None) -> None:
    """
    Immediate check that raises MemoryError if limit is exceeded.
    Equivalent to check_memory_limit.
    """
    check_memory_limit(threshold_bytes)