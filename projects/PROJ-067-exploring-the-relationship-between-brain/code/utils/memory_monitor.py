"""
Memory monitoring utilities to enforce RAM constraints (<7GB).
"""
import os
import time
from typing import Optional

class MemoryLimitExceededError(Exception):
    """Raised when memory usage exceeds the defined limit."""
    pass

# Default limit: 7GB in bytes
MAX_MEMORY_BYTES = 7 * 1024 * 1024 * 1024 

def get_current_rss_bytes() -> int:
    """
    Get current Resident Set Size (RSS) in bytes from /proc/self/status.
    Returns 0 if not available (e.g., on non-Linux systems).
    """
    if os.name != 'posix':
        # Fallback for non-Linux systems (approximate)
        return 0
    
    try:
        with open('/proc/self/status', 'r') as f:
            for line in f:
                if line.startswith('VmRSS:'):
                    # Format: VmRSS:     12345 kB
                    parts = line.split()
                    kb_value = int(parts[1])
                    return kb_value * 1024
    except (FileNotFoundError, ValueError, IndexError):
        return 0
    
    return 0

def check_memory_limit(limit_bytes: Optional[int] = None) -> bool:
    """
    Check if current RSS exceeds the limit.
    Returns True if OK, raises MemoryLimitExceededError if exceeded.
    """
    limit = limit_bytes if limit_bytes is not None else MAX_MEMORY_BYTES
    current_rss = get_current_rss_bytes()
    
    if current_rss > limit:
        raise MemoryLimitExceededError(
            f"Memory limit exceeded: Current RSS {current_rss / (1024**3):.2f}GB "
            f"exceeds limit {limit / (1024**3):.2f}GB"
        )
    return True

def assert_memory_limit(limit_bytes: Optional[int] = None) -> None:
    """
    Wrapper for check_memory_limit that ensures an exception is raised on failure.
    """
    check_memory_limit(limit_bytes)

class MemoryMonitor:
    """
    Context manager or utility class to monitor memory over time.
    """
    def __init__(self, limit_bytes: Optional[int] = None, interval_seconds: float = 1.0):
        self.limit = limit_bytes if limit_bytes is not None else MAX_MEMORY_BYTES
        self.interval = interval_seconds
        self.history = []

    def check(self) -> bool:
        """Perform a single check."""
        return check_memory_limit(self.limit)

    def start(self) -> None:
        """Start monitoring (optional background thread could be implemented here)."""
        pass

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        return False
