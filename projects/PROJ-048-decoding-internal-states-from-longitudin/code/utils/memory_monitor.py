import os
import sys
from typing import Optional

class MemoryExceededError(Exception):
    """Raised when memory usage exceeds the configured limit."""
    pass

def get_memory_limit_gb() -> float:
    """
    Retrieve the memory limit in GB from the environment or config.
    Defaults to 5.0 GB if not specified (per FR-001/SC-001).
    """
    limit_str = os.getenv("MEMORY_LIMIT_GB", "5.0")
    try:
        return float(limit_str)
    except ValueError:
        return 5.0

def get_current_memory_usage_gb() -> float:
    """
    Estimate current memory usage of the process in GB.
    Uses /proc/self/status on Linux, psutil if available, or falls back to 0.0.
    """
    # Try psutil first if available (common in research environments)
    try:
        import psutil
        process = psutil.Process(os.getpid())
        return process.memory_info().rss / (1024 ** 3)
    except ImportError:
        pass
    
    # Fallback to /proc on Linux
    if sys.platform.startswith("linux"):
        try:
            with open(f"/proc/{os.getpid()}/status", "r") as f:
                for line in f:
                    if line.startswith("VmRSS:"):
                        # Value is in kB
                        val = int(line.split()[1])
                        return val / (1024 * 1024) # kB to GB
        except (FileNotFoundError, IndexError, ValueError):
            pass
    
    # Fallback: cannot determine, assume 0.0 to avoid false positives, 
    # but logging should warn.
    return 0.0

def check_memory_limit(required_gb: Optional[float] = None) -> None:
    """
    Check if current memory usage (plus optional required_gb) exceeds the limit.
    
    Raises:
        MemoryExceededError: If the limit is exceeded.
    """
    limit = get_memory_limit_gb()
    current = get_current_memory_usage_gb()
    
    # If required_gb is provided, check if current + required > limit
    # If not provided, just check if current > limit (safety check)
    check_val = current + (required_gb if required_gb else 0)
    
    if check_val > limit:
        raise MemoryExceededError(
            f"Memory limit exceeded: Current usage {current:.2f}GB "
            f"(+ required {required_gb:.2f}GB) exceeds limit of {limit}GB"
        )

class MemoryMonitor:
    """Context manager to monitor memory usage within a block."""
    
    def __init__(self, limit_gb: Optional[float] = None):
        self.limit_gb = limit_gb
        self.start_usage = 0.0
    
    def __enter__(self):
        self.start_usage = get_current_memory_usage_gb()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        end_usage = get_current_memory_usage_gb()
        delta = end_usage - self.start_usage
        limit = self.limit_gb if self.limit_gb is not None else get_memory_limit_gb()
        
        if end_usage > limit:
            raise MemoryExceededError(
                f"Memory limit exceeded: Usage rose to {end_usage:.2f}GB "
                f"(delta: {delta:.2f}GB), limit is {limit}GB"
            )
        return False
