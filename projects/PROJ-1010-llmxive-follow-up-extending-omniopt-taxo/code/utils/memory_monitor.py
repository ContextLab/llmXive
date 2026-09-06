"""
Memory monitoring utility for the llmXive automated science pipeline.

Provides tools to track, log, and enforce memory usage constraints during
long-running research tasks (e.g., spectral extraction, dataset streaming).

Features:
- Real-time memory tracking using `psutil`.
- Context manager for scoped memory monitoring.
- Hard enforcement of memory limits with automatic cleanup/logging.
- Integration with the project's structured logging system.
"""

import os
import gc
import time
import threading
from typing import Optional, Callable, Dict, Any, List
from contextlib import contextmanager

try:
    import psutil
except ImportError:
    raise ImportError(
        "psutil is required for memory monitoring. "
        "Please install it via `pip install psutil` or ensure it is in requirements.txt."
    )

# Import project logging utilities
from utils.logging import get_logger, info, warning, error, debug, configure_logging

# Initialize logger for this module
logger = get_logger(__name__)

# Constants
DEFAULT_LIMIT_MB = 7000  # Default 7GB limit as per project constraints
SAMPLE_INTERVAL_SEC = 1.0


class MemoryMonitor:
    """
    Monitors the memory usage of the current process and optionally child processes.

    Attributes:
        limit_mb (float): The memory limit in Megabytes.
        process (psutil.Process): The current process object.
        history (List[Dict]): List of recorded memory snapshots.
        _stop_event (threading.Event): Signal to stop background sampling.
        _thread (threading.Thread): Background sampling thread.
    """

    def __init__(self, limit_mb: float = DEFAULT_LIMIT_MB, sample_interval: float = SAMPLE_INTERVAL_SEC):
        """
        Initializes the memory monitor.

        Args:
            limit_mb: Maximum allowed memory usage in MB.
            sample_interval: Interval in seconds for background sampling.
        """
        self.limit_mb = limit_mb
        self.process = psutil.Process(os.getpid())
        self.history: List[Dict[str, Any]] = []
        self._sample_interval = sample_interval
        self._stop_event = threading.Event()
        self._thread: Optional[threading.Thread] = None
        self._start_time: Optional[float] = None
        self._peak_mb: float = 0.0

    def _sample(self) -> Dict[str, Any]:
        """
        Collects current memory statistics.

        Returns:
            A dictionary containing current memory stats.
        """
        try:
            mem_info = self.process.memory_info()
            current_mb = mem_info.rss / (1024 * 1024)
            self._peak_mb = max(self._peak_mb, current_mb)

            snapshot = {
                "timestamp": time.time(),
                "elapsed_sec": time.time() - self._start_time if self._start_time else 0.0,
                "rss_mb": current_mb,
                "vms_mb": mem_info.vms / (1024 * 1024),
                "percent": self.process.memory_percent(),
                "peak_mb": self._peak_mb,
                "limit_mb": self.limit_mb
            }

            # Check limit
            if current_mb > self.limit_mb:
                error(
                    "Memory limit exceeded",
                    current_mb=current_mb,
                    limit_mb=self.limit_mb,
                    percent=snapshot["percent"]
                )
                self._check_and_handle_exceed()

            return snapshot
        except psutil.NoSuchProcess:
            error("Process no longer exists during memory sampling.")
            return {}

    def _check_and_handle_exceed(self):
        """
        Handles the event where memory limit is exceeded.
        Currently logs and raises an exception to fail loudly.
        """
        # Force garbage collection as a last resort before failing
        gc.collect()
        # Re-check immediately
        try:
            current_mb = self.process.memory_info().rss / (1024 * 1024)
            if current_mb > self.limit_mb:
                raise MemoryError(
                    f"Memory limit of {self.limit_mb:.2f}MB exceeded. "
                    f"Current usage: {current_mb:.2f}MB. "
                    f"Process terminated to prevent system instability."
                )
        except Exception as e:
            error(f"Failed to recover from memory limit: {e}")
            raise

    def _background_loop(self):
        """Background thread loop for sampling."""
        while not self._stop_event.is_set():
            snapshot = self._sample()
            if snapshot:
                self.history.append(snapshot)
            self._stop_event.wait(self._sample_interval)

    def start(self):
        """Starts the background memory monitoring thread."""
        if self._thread is not None and self._thread.is_alive():
            return

        self._start_time = time.time()
        self._stop_event.clear()
        self._peak_mb = 0.0
        self.history = []

        self._thread = threading.Thread(target=self._background_loop, daemon=True)
        self._thread.start()
        info("Memory monitoring started.", limit_mb=self.limit_mb)

    def stop(self) -> Dict[str, Any]:
        """
        Stops the background monitoring and returns summary statistics.

        Returns:
            A dictionary with peak usage, average usage, and total duration.
        """
        if self._thread is None:
            return {"status": "not_started"}

        self._stop_event.set()
        if self._thread.is_alive():
            self._thread.join(timeout=2.0)

        summary = {
            "peak_mb": self._peak_mb,
            "limit_mb": self.limit_mb,
            "samples_collected": len(self.history),
            "duration_sec": time.time() - self._start_time if self._start_time else 0.0,
            "history": self.history
        }

        if self._peak_mb > self.limit_mb:
            warning(
                "Memory limit exceeded during monitoring.",
                peak_mb=self._peak_mb,
                limit_mb=self.limit_mb
            )
        else:
            info(
                "Memory monitoring completed successfully.",
                peak_mb=self._peak_mb,
                limit_mb=self.limit_mb
            )

        return summary

    def get_current_mb(self) -> float:
        """Returns the current RSS memory in MB."""
        return self.process.memory_info().rss / (1024 * 1024)


@contextmanager
def monitor_memory(limit_mb: float = DEFAULT_LIMIT_MB, sample_interval: float = SAMPLE_INTERVAL_SEC):
    """
    Context manager to monitor memory usage within a specific code block.

    Usage:
        with monitor_memory(limit_mb=4096) as stats:
            # Do heavy computation
            pass
        print(stats['peak_mb'])

    Args:
        limit_mb: Memory limit in MB.
        sample_interval: Sampling interval in seconds.

    Yields:
        MemoryMonitor instance.

    Raises:
        MemoryError: If the memory limit is exceeded.
    """
    monitor = MemoryMonitor(limit_mb=limit_mb, sample_interval=sample_interval)
    monitor.start()
    try:
        yield monitor
    finally:
        monitor.stop()


def enforce_memory_limit(limit_mb: float = DEFAULT_LIMIT_MB, check_interval: float = 0.5):
    """
    A blocking check loop that raises MemoryError if the limit is exceeded.
    Useful for long-running loops that cannot use the context manager directly.

    Args:
        limit_mb: The memory limit in MB.
        check_interval: How often to check (seconds).
    """
    process = psutil.Process(os.getpid())
    start = time.time()

    while True:
        mem_mb = process.memory_info().rss / (1024 * 1024)
        if mem_mb > limit_mb:
            error(
                "Hard memory limit exceeded in enforce_memory_limit.",
                current_mb=mem_mb,
                limit_mb=limit_mb
            )
            raise MemoryError(
                f"Hard limit {limit_mb}MB exceeded. Current: {mem_mb:.2f}MB."
            )
        time.sleep(check_interval)


# Convenience function for quick checks
def check_memory_usage(limit_mb: float = DEFAULT_LIMIT_MB) -> bool:
    """
    Checks if current memory usage is within the limit.

    Args:
        limit_mb: The limit in MB.

    Returns:
        True if within limit, False otherwise.
    """
    process = psutil.Process(os.getpid())
    current_mb = process.memory_info().rss / (1024 * 1024)
    is_safe = current_mb <= limit_mb

    if not is_safe:
        error(
            "Memory check failed.",
            current_mb=current_mb,
            limit_mb=limit_mb
        )
    else:
        debug(
            "Memory check passed.",
            current_mb=current_mb,
            limit_mb=limit_mb
        )

    return is_safe