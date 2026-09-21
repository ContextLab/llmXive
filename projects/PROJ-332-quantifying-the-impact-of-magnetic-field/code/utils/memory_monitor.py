"""
Memory monitoring utilities for tracking resource usage during pipeline execution.

This module provides classes and functions for monitoring memory consumption
throughout the execution of the analysis pipeline. It supports continuous
monitoring, threshold checking, and reporting of peak memory usage.

Classes:
    MemoryMonitor: Context manager and utility class for tracking memory usage.

Functions:
    verify_memory_footprint: Check if peak memory usage is within acceptable limits.
    main: Entry point for running the memory monitor as a script.

Example:
    >>> from utils.memory_monitor import MemoryMonitor
    >>> with MemoryMonitor() as monitor:
    ...     # Perform memory-intensive operations
    ...     process_large_dataset()
    ...     print(f"Peak memory: {monitor.peak_memory_mb:.2f} MB")
"""

import os
import sys
import resource
import logging
import time
import json
from threading import Thread, Event
from typing import Optional, List, Dict, Any
from pathlib import Path

logger = logging.getLogger(__name__)


class MemoryMonitor:
    """
    A context manager and utility class for monitoring memory usage.

    This class provides functionality to:
    - Continuously sample memory usage at specified intervals
    - Track peak memory consumption
    - Check against memory thresholds
    - Export memory usage statistics to JSON

    Attributes:
        sample_interval: Time between memory samples in seconds.
        peak_memory_mb: Highest memory usage observed during monitoring.
        samples: List of (timestamp, memory_mb) tuples.

    Example:
        >>> monitor = MemoryMonitor(sample_interval=1.0)
        >>> with monitor:
        ...     process_data()
        >>> print(f"Peak: {monitor.peak_memory_mb:.2f} MB")
    """

    def __init__(self, sample_interval: float = 1.0, enable_monitoring: bool = True):
        """
        Initialize the memory monitor.

        Args:
            sample_interval: Time between memory samples in seconds (default 1.0).
            enable_monitoring: Whether to start background monitoring thread (default True).
        """
        self.sample_interval = sample_interval
        self.enable_monitoring = enable_monitoring
        self.peak_memory_mb = 0.0
        self.samples: List[Dict[str, float]] = []
        self._stop_event = Event()
        self._monitor_thread: Optional[Thread] = None
        self._start_time: Optional[float] = None

    def _get_current_memory_mb(self) -> float:
        """
        Get the current memory usage of the process in megabytes.

        Returns:
            Current memory usage in megabytes.
        """
        usage = resource.getrusage(resource.RUSAGE_SELF)
        # ru_maxrss is in kilobytes on Linux
        maxrss_kb = usage.ru_maxrss
        return maxrss_kb / 1024.0

    def _monitor_loop(self):
        """
        Background thread function for continuous memory monitoring.

        This method runs in a separate thread, periodically sampling memory
        usage until the stop event is set.
        """
        while not self._stop_event.is_set():
            current_memory = self._get_current_memory_mb()
            timestamp = time.time()

            # Update peak memory
            if current_memory > self.peak_memory_mb:
                self.peak_memory_mb = current_memory

            # Store sample
            self.samples.append({
                'timestamp': timestamp,
                'memory_mb': current_memory
            })

            # Wait for next sample
            self._stop_event.wait(self.sample_interval)

    def start(self):
        """
        Start background memory monitoring.

        This begins a separate thread that continuously samples memory usage.
        """
        if not self.enable_monitoring:
            return

        self._start_time = time.time()
        self._stop_event.clear()
        self._monitor_thread = Thread(target=self._monitor_loop, daemon=True)
        self._monitor_thread.start()
        logger.debug("Memory monitoring started")

    def stop(self):
        """
        Stop background memory monitoring.

        This signals the monitoring thread to stop and waits for it to finish.
        """
        if self._monitor_thread is not None:
            self._stop_event.set()
            self._monitor_thread.join(timeout=2.0)
            logger.debug("Memory monitoring stopped")

    def __enter__(self):
        """Context manager entry: start monitoring."""
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit: stop monitoring."""
        self.stop()
        return False

    def get_stats(self) -> Dict[str, Any]:
        """
        Get summary statistics about memory usage.

        Returns:
            Dictionary containing:
                - peak_memory_mb: Highest memory usage observed
                - current_memory_mb: Most recent memory reading
                - sample_count: Number of samples collected
                - duration_seconds: Total monitoring duration
                - avg_memory_mb: Average memory usage (if samples exist)
        """
        stats = {
            'peak_memory_mb': self.peak_memory_mb,
            'current_memory_mb': self._get_current_memory_mb(),
            'sample_count': len(self.samples),
            'duration_seconds': time.time() - self._start_time if self._start_time else 0.0
        }

        if self.samples:
            avg_memory = sum(s['memory_mb'] for s in self.samples) / len(self.samples)
            stats['avg_memory_mb'] = avg_memory
            stats['min_memory_mb'] = min(s['memory_mb'] for s in self.samples)

        return stats

    def export_to_json(self, output_path: Path):
        """
        Export memory usage statistics to a JSON file.

        Args:
            output_path: Path where the JSON file will be saved.
        """
        stats = self.get_stats()
        stats['samples'] = self.samples

        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w') as f:
            json.dump(stats, f, indent=2)

        logger.info(f"Memory stats exported to {output_path}")


def verify_memory_footprint(
    limit_mb: float,
    monitor: Optional[MemoryMonitor] = None,
    strict: bool = True
) -> bool:
    """
    Verify that peak memory usage is within the specified limit.

    Args:
        limit_mb: Maximum allowed memory usage in megabytes.
        monitor: Optional MemoryMonitor instance. If None, a new one is created.
        strict: If True, raise an exception on failure. If False, return False.

    Returns:
        True if memory usage is within limits, False otherwise.

    Raises:
        MemoryError: If strict=True and memory limit is exceeded.
    """
    if monitor is None:
        monitor = MemoryMonitor()

    # If monitor is already running, use its peak
    # Otherwise, take a single snapshot
    if monitor.peak_memory_mb > 0:
        peak = monitor.peak_memory_mb
    else:
        peak = monitor._get_current_memory_mb()

    if peak > limit_mb:
        error_msg = f"Memory limit exceeded: {peak:.2f} MB > {limit_mb} MB"
        if strict:
            raise MemoryError(error_msg)
        else:
            logger.warning(error_msg)
            return False

    logger.info(f"Memory usage within limits: {peak:.2f} MB <= {limit_mb} MB")
    return True


def main():
    """
    Main entry point for the memory monitor module.

    This function demonstrates the usage of the MemoryMonitor class
    with a simulated memory-intensive operation.
    """
    logger.info("Running utils/memory_monitor.py as a script (demo mode)")

    limit_mb = 4096  # 4 GB limit
    monitor = MemoryMonitor(sample_interval=0.5)

    try:
        with monitor:
            # Simulate some work
            logger.info("Simulating memory-intensive operation...")
            data = []
            for i in range(100):
                # Allocate some memory
                chunk = [0] * 100000
                data.append(chunk)
                time.sleep(0.1)

            # Get stats
            stats = monitor.get_stats()
            logger.info(f"Peak memory: {stats['peak_memory_mb']:.2f} MB")
            logger.info(f"Samples collected: {stats['sample_count']}")

            # Verify against limit
            if verify_memory_footprint(limit_mb, monitor, strict=False):
                logger.info("Memory usage is acceptable")
            else:
                logger.warning("Memory usage exceeded limit")

    except MemoryError as e:
        logger.error(f"Memory limit exceeded: {e}")
        raise
    finally:
        # Export stats
        output_path = Path('outputs/memory_stats.json')
        monitor.export_to_json(output_path)
        logger.info(f"Memory stats saved to {output_path}")
