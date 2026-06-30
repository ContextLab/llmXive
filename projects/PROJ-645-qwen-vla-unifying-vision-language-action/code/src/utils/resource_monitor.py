"""
Resource monitoring utility using psutil for RAM and wall-time tracking.

This module provides context managers and utility functions to monitor
system resources (specifically RAM usage) and execution time during
training and evaluation loops.

Constraints:
- RAM limit: 7GB (warn at 6.5GB, error at 7GB)
- Wall-time limit: Configurable (default 6 hours for training)
"""
import os
import time
import logging
from contextlib import contextmanager
from typing import Optional, Dict, Any, Generator
import psutil
import threading

# Constants
RAM_LIMIT_GB = 7.0
RAM_WARNING_THRESHOLD_GB = 6.5
DEFAULT_WALL_TIME_LIMIT_SECONDS = 21600  # 6 hours

logger = logging.getLogger(__name__)


class ResourceMonitor:
    """
    Monitors system resources (RAM, wall-time) for training loops.
    
    Attributes:
        start_time: Timestamp when monitoring started.
        peak_ram_gb: Peak RAM usage observed (in GB).
        wall_time_limit: Maximum allowed wall time in seconds.
        ram_limit_gb: Maximum allowed RAM in GB.
    """
    
    def __init__(
        self,
        wall_time_limit: float = DEFAULT_WALL_TIME_LIMIT_SECONDS,
        ram_limit_gb: float = RAM_LIMIT_GB,
        warning_threshold_gb: float = RAM_WARNING_THRESHOLD_GB
    ):
        """
        Initialize the resource monitor.
        
        Args:
            wall_time_limit: Maximum allowed execution time in seconds.
            ram_limit_gb: Maximum allowed RAM usage in GB.
            warning_threshold_gb: RAM threshold to trigger warnings.
        """
        self.start_time: Optional[float] = None
        self.peak_ram_gb: float = 0.0
        self.wall_time_limit = wall_time_limit
        self.ram_limit_gb = ram_limit_gb
        self.warning_threshold_gb = warning_threshold_gb
        self._lock = threading.Lock()
        self._timeout_triggered = False

    def start(self) -> None:
        """Start the monitoring timer."""
        self.start_time = time.time()
        self.peak_ram_gb = 0.0
        self._timeout_triggered = False
        logger.info("Resource monitoring started.")

    def stop(self) -> None:
        """Stop the monitoring timer and log final stats."""
        elapsed = self.elapsed_time
        logger.info(
            f"Resource monitoring stopped. "
            f"Elapsed time: {elapsed:.2f}s, "
            f"Peak RAM: {self.peak_ram_gb:.2f}GB"
        )

    @property
    def elapsed_time(self) -> float:
        """Get the elapsed wall time since start."""
        if self.start_time is None:
            return 0.0
        return time.time() - self.start_time

    def get_current_ram_gb(self) -> float:
        """
        Get current process RAM usage in GB.
        
        Returns:
            Current RAM usage in GB.
        """
        process = psutil.Process(os.getpid())
        mem_info = process.memory_info()
        return mem_info.rss / (1024 ** 3)

    def check_resources(self) -> Dict[str, Any]:
        """
        Check current resource usage and update peak metrics.
        
        Returns:
            Dictionary with current and peak resource stats.
        """
        current_ram = self.get_current_ram_gb()
        with self._lock:
            if current_ram > self.peak_ram_gb:
                self.peak_ram_gb = current_ram

        stats = {
            "current_ram_gb": current_ram,
            "peak_ram_gb": self.peak_ram_gb,
            "elapsed_time_seconds": self.elapsed_time,
            "ram_limit_gb": self.ram_limit_gb,
            "wall_time_limit_seconds": self.wall_time_limit
        }

        # Check thresholds
        if current_ram >= self.ram_limit_gb:
            logger.error(
                f"CRITICAL: RAM usage {current_ram:.2f}GB exceeds limit "
                f"{self.ram_limit_gb}GB. Terminating."
            )
            raise MemoryError(f"RAM limit exceeded: {current_ram:.2f}GB")
        
        if current_ram >= self.warning_threshold_gb:
            logger.warning(
                f"WARNING: RAM usage {current_ram:.2f}GB exceeds threshold "
                f"{self.warning_threshold_gb}GB."
            )

        if self.elapsed_time >= self.wall_time_limit:
            if not self._timeout_triggered:
                logger.warning("TIMEOUT_WARNING: Wall-time limit reached.")
                self._timeout_triggered = True
            # Do not abort, just warn per spec

        return stats

    def is_timed_out(self) -> bool:
        """Check if the wall-time limit has been exceeded."""
        return self.elapsed_time >= self.wall_time_limit

    def get_status(self) -> str:
        """
        Get a human-readable status string.
        
        Returns:
            Status string with time and RAM info.
        """
        return (
            f"Time: {self.elapsed_time:.1f}s / {self.wall_time_limit}s, "
            f"RAM: {self.peak_ram_gb:.2f}GB (Peak)"
        )


@contextmanager
def resource_monitor_context(
    wall_time_limit: float = DEFAULT_WALL_TIME_LIMIT_SECONDS,
    ram_limit_gb: float = RAM_LIMIT_GB,
    warning_threshold_gb: float = RAM_WARNING_THRESHOLD_GB
) -> Generator[ResourceMonitor, None, None]:
    """
    Context manager for resource monitoring.
    
    Usage:
        with resource_monitor_context(wall_time_limit=3600) as monitor:
            while not monitor.is_timed_out():
                monitor.check_resources()
                # ... training step ...
    
    Args:
        wall_time_limit: Max time in seconds.
        ram_limit_gb: Max RAM in GB.
        warning_threshold_gb: RAM warning threshold.
        
    Yields:
        ResourceMonitor instance.
    """
    monitor = ResourceMonitor(
        wall_time_limit=wall_time_limit,
        ram_limit_gb=ram_limit_gb,
        warning_threshold_gb=warning_threshold_gb
    )
    monitor.start()
    try:
        yield monitor
    finally:
        monitor.stop()