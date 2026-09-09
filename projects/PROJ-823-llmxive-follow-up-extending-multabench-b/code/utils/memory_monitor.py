"""Memory monitoring utilities for the llmXive pipeline.

Provides functions and context managers to track peak RAM usage and enforce
memory limits during pipeline execution.
"""
from __future__ import annotations

import functools
import os
import time
from contextlib import contextmanager
from typing import Callable, Optional

import psutil


class MemoryMonitor:
    """Tracks peak memory usage of the current process.

    This class provides a simple interface to monitor memory usage over time
    and determine if a process exceeds a specified limit.
    """

    def __init__(self, limit_mb: float = 6500):
        """Initialize the memory monitor.

        Args:
            limit_mb: Maximum allowed memory in MB (default: 6500 MB).
        """
        self.limit_mb = limit_mb
        self.process = psutil.Process(os.getpid())
        self.peak_memory_mb = 0.0
        self.start_time: Optional[float] = None
        self._monitoring = False

    def get_current_memory_mb(self) -> float:
        """Get the current memory usage of the process in MB.

        Returns:
            Current memory usage in MB.
        """
        current_mb = self.process.memory_info().rss / 1024 / 1024
        if current_mb > self.peak_memory_mb:
            self.peak_memory_mb = current_mb
        return current_mb

    def get_peak_memory_mb(self) -> float:
        """Get the peak memory usage observed since initialization.

        Returns:
            Peak memory usage in MB.
        """
        return self.peak_memory_mb

    def check_limit(self) -> bool:
        """Check if current memory usage is within the limit.

        Returns:
            True if within limit, False otherwise.
        """
        current = self.get_current_memory_mb()
        return current <= self.limit_mb

    def assert_limit(self) -> None:
        """Assert that memory usage is within the limit.

        Raises:
            MemoryError: If memory usage exceeds the limit.
        """
        current = self.get_current_memory_mb()
        if current > self.limit_mb:
            raise MemoryError(
                f"Memory limit ({self.limit_mb}MB) exceeded. "
                f"Current: {current:.2f}MB, Peak: {self.peak_memory_mb:.2f}MB"
            )

    def start_monitoring(self) -> None:
        """Start tracking memory usage."""
        self.start_time = time.time()
        self._monitoring = True
        # Initialize peak with current value
        self.get_current_memory_mb()

    def stop_monitoring(self) -> dict:
        """Stop monitoring and return summary statistics.

        Returns:
            Dictionary with monitoring statistics.
        """
        self._monitoring = False
        elapsed = time.time() - self.start_time if self.start_time else 0
        return {
            "peak_memory_mb": self.peak_memory_mb,
            "limit_mb": self.limit_mb,
            "elapsed_seconds": elapsed,
            "within_limit": self.peak_memory_mb <= self.limit_mb
        }


def get_process_memory_mb() -> float:
    """Returns the current memory usage of the process in MB.

    This is a convenience function that creates a temporary monitor
    and returns the current value.

    Returns:
        Current memory usage in MB.
    """
    process = psutil.Process(os.getpid())
    return process.memory_info().rss / 1024 / 1024


@contextmanager
def memory_limit_context(limit_mb: float = 6500):
    """Context manager to check memory usage against a limit.

    This context manager checks memory usage at entry and exit.
    If the limit is exceeded at any point, a MemoryError is raised.

    Args:
        limit_mb: Maximum allowed memory in MB.

    Yields:
        None

    Raises:
        MemoryError: If memory usage exceeds the limit.
    """
    monitor = MemoryMonitor(limit_mb=limit_mb)
    monitor.start_monitoring()
    try:
        yield monitor
        # Check at exit
        monitor.assert_limit()
    finally:
        monitor.stop_monitoring()


def memory_limit_decorator(limit_mb: float = 6500):
    """Decorator to enforce memory limits on functions.

    Args:
        limit_mb: Maximum allowed memory in MB.

    Returns:
        Decorator function.
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            with memory_limit_context(limit_mb=limit_mb) as monitor:
                result = func(*args, **kwargs)
                return result
        return wrapper
    return decorator