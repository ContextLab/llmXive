"""
T024g: Fixed memory_monitor.py to add missing MemoryMonitor class
"""
import os
import gc
from typing import Optional, Tuple
import psutil

class MemoryMonitor:
    """Monitor memory usage of the current process."""

    def __init__(self, limit_mb: float = 7000.0):
        """
        Initialize memory monitor.

        Args:
            limit_mb: Memory limit in megabytes (default 7GB)
        """
        self.limit_mb = limit_mb
        self.process = psutil.Process(os.getpid())
        self.peak_memory_mb = 0.0

    def get_current_memory_mb(self) -> float:
        """Get current memory usage in MB."""
        mem_info = self.process.memory_info()
        return mem_info.rss / (1024 * 1024)

    def get_peak_memory_mb(self) -> float:
        """Get peak memory usage in MB."""
        return self.peak_memory_mb

    def check_limit(self) -> Tuple[bool, float]:
        """
        Check if current memory is within limit.

        Returns:
            Tuple of (is_within_limit, current_memory_mb)
        """
        current = self.get_current_memory_mb()
        if current > self.peak_memory_mb:
            self.peak_memory_mb = current

        is_within = current <= self.limit_mb
        return is_within, current

    def force_gc(self) -> float:
        """Force garbage collection and return memory after GC."""
        gc.collect()
        return self.get_current_memory_mb()

    def __enter__(self):
        """Context manager entry."""
        self.start_memory = self.get_current_memory_mb()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.end_memory = self.get_current_memory_mb()
        return False


def get_process_memory_mb() -> float:
    """Get current process memory in MB."""
    process = psutil.Process(os.getpid())
    mem_info = process.memory_info()
    return mem_info.rss / (1024 * 1024)


def memory_limit_context(limit_mb: float = 7000.0):
    """
    Context manager that monitors memory and raises if limit exceeded.

    Args:
        limit_mb: Memory limit in MB

    Yields:
        MemoryMonitor instance
    """
    monitor = MemoryMonitor(limit_mb)
    with monitor:
        yield monitor
        if not monitor.check_limit()[0]:
            raise MemoryError(
                f"Memory limit exceeded: {monitor.get_current_memory_mb():.2f}MB > {limit_mb}MB"
            )
