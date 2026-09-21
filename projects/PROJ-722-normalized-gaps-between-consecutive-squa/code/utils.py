"""
Utility functions for memory monitoring and management.

Provides tools to track RSS (Resident Set Size) memory usage and enforce
memory limits to prevent out-of-memory crashes during large computations.
"""

import os
from typing import Optional

def get_current_rss_bytes() -> int:
    """
    Get the current Resident Set Size (RSS) memory usage in bytes.

    Reads from /proc/self/status on Linux or uses resource module on other
    Unix systems. Falls back to 0 if the method is not supported.

    Returns:
        Current RSS in bytes, or 0 if measurement is unavailable.
    """
    try:
        # Linux specific - most accurate
        with open('/proc/self/status', 'r') as f:
            for line in f:
                if line.startswith('VmRSS:'):
                    # Format: "VmRSS:    12345 kB"
                    parts = line.split()
                    if len(parts) >= 2:
                        return int(parts[1]) * 1024  # Convert kB to bytes
    except (FileNotFoundError, ValueError, IndexError):
        pass

    # Fallback: try resource module (Unix)
    try:
        import resource
        rusage = resource.getrusage(resource.RUSAGE_SELF)
        # ru_maxrss is in KB on Linux, but bytes on macOS
        # We'll assume KB for consistency and convert
        return rusage.ru_maxrss * 1024
    except ImportError:
        pass

    return 0

class MemoryMonitor:
    """
    A context manager and utility class to monitor peak memory usage.

    Tracks the maximum RSS observed during its lifetime, allowing
    detection of memory spikes that could indicate leaks or inefficiencies.
    """

    def __init__(self):
        self._peak_rss: Optional[int] = None
        self._start_rss: Optional[int] = None
        self._is_running: bool = False

    def start(self) -> int:
        """
        Start monitoring and record the initial RSS.

        Returns:
            The initial RSS in bytes.
        """
        self._start_rss = get_current_rss_bytes()
        self._peak_rss = self._start_rss
        self._is_running = True
        return self._start_rss

    def get_current_rss(self) -> int:
        """
        Get the current RSS.

        Returns:
            Current RSS in bytes.
        """
        return get_current_rss_bytes()

    def update_peak(self) -> int:
        """
        Update the peak RSS if current usage is higher.

        Returns:
            The current peak RSS in bytes.
        """
        current = self.get_current_rss()
        if self._peak_rss is None or current > self._peak_rss:
            self._peak_rss = current
        return self._peak_rss

    def stop(self) -> int:
        """
        Stop monitoring and return the peak RSS observed.

        Returns:
            The peak RSS in bytes since start() was called.
        """
        self._is_running = False
        self.update_peak()
        return self._peak_rss if self._peak_rss is not None else 0

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop()
        return False

def check_memory_limit(
    current_rss: int,
    limit_bytes: int,
    logger: Optional[object] = None
) -> None:
    """
    Check if current RSS exceeds the specified limit.

    If the limit is exceeded, this function logs a warning (if logger provided)
    and raises an AssertionError to fail the process immediately, satisfying
    the "fail loudly" requirement for memory constraints.

    Args:
        current_rss: Current RSS usage in bytes.
        limit_bytes: Maximum allowed RSS in bytes.
        logger: Optional logger instance for logging warnings.

    Raises:
        AssertionError: If current_rss exceeds limit_bytes.
    """
    if current_rss > limit_bytes:
        msg = (
            f"Memory limit exceeded: current RSS {current_rss / 1e6:.2f} MB "
            f"exceeds limit {limit_bytes / 1e6:.2f} MB"
        )
        if logger:
            logger.warning(msg)
        raise AssertionError(msg)
