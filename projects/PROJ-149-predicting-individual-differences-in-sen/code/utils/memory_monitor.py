"""
Memory Monitor Utility for EEG Pipeline.

This module provides a MemoryMonitor class that wraps script execution,
logs memory usage (max_rss) and elapsed_time to a temp file every 1 second,
and raises an error if RAM usage exceeds a configurable threshold (default 6GB).

It is designed to be used as a context manager or decorator to monitor
resource consumption during heavy data processing tasks.
"""

import os
import sys
import time
import threading
import tempfile
import json
import signal
from typing import Optional, Callable, Any
from pathlib import Path

try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False
    # Fallback to /proc on Linux if psutil is not available
    if sys.platform.startswith('linux'):
        def get_process_memory_mb(pid: int) -> float:
            try:
                with open(f'/proc/{pid}/statm', 'r') as f:
                    pages = int(f.read().split()[1])
                    # Page size is typically 4096 bytes
                    return (pages * 4096) / (1024 * 1024)
            except (FileNotFoundError, IndexError, ValueError):
                return 0.0
    else:
        def get_process_memory_mb(pid: int) -> float:
            return 0.0


class MemoryMonitor:
    """
    A context manager and decorator to monitor memory usage of a process.

    Attributes:
        max_rss_mb (float): The maximum RSS (Resident Set Size) observed in MB.
        elapsed_time (float): Total elapsed time in seconds.
        log_file (str): Path to the temporary log file.
        threshold_gb (float): RAM threshold in GB. If exceeded, raises MemoryError.
        interval (float): Sampling interval in seconds.
    """

    def __init__(
        self,
        log_file: Optional[str] = None,
        threshold_gb: float = 6.0,
        interval: float = 1.0
    ):
        """
        Initialize the MemoryMonitor.

        Args:
            log_file: Path to the log file. If None, a temporary file is created.
            threshold_gb: Maximum allowed RAM usage in GB. Default is 6.0 GB.
            interval: Sampling interval in seconds. Default is 1.0 second.
        """
        self.threshold_gb = threshold_gb
        self.interval = interval
        self.log_file = log_file or os.path.join(tempfile.gettempdir(), "memory_monitor_log.json")
        self.max_rss_mb = 0.0
        self.elapsed_time = 0.0
        self._stop_event = threading.Event()
        self._thread: Optional[threading.Thread] = None
        self._start_time: float = 0.0
        self._process = psutil.Process() if PSUTIL_AVAILABLE else None

    def _get_current_memory_mb(self) -> float:
        """Get current memory usage in MB."""
        if PSUTIL_AVAILABLE and self._process:
            return self._process.memory_info().rss / (1024 * 1024)
        else:
            # Fallback for Linux without psutil
            return get_process_memory_mb(os.getpid())

    def _monitor_loop(self) -> None:
        """Background loop to sample memory and log it."""
        while not self._stop_event.is_set():
            current_rss = self._get_current_memory_mb()
            if current_rss > self.max_rss_mb:
                self.max_rss_mb = current_rss

            # Check threshold
            if current_rss / (1024 * 1024 * 1024) > self.threshold_gb:
                raise MemoryError(
                    f"Memory threshold exceeded: {current_rss / (1024 * 1024 * 1024):.2f} GB > {self.threshold_gb} GB"
                )

            # Log to file
            log_entry = {
                "timestamp": time.time(),
                "elapsed": time.time() - self._start_time,
                "rss_mb": current_rss
            }
            try:
                with open(self.log_file, 'a') as f:
                    f.write(json.dumps(log_entry) + '\n')
            except IOError:
                pass  # Ignore logging errors to avoid disrupting the main process

            self._stop_event.wait(self.interval)

    def __enter__(self) -> 'MemoryMonitor':
        """Start the monitoring thread."""
        self._start_time = time.time()
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self._thread.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Stop the monitoring thread and finalize logs."""
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=2.0)
        
        self.elapsed_time = time.time() - self._start_time

        # Write final summary to log file
        summary = {
            "final": True,
            "max_rss_mb": self.max_rss_mb,
            "elapsed_time_sec": self.elapsed_time,
            "threshold_gb": self.threshold_gb,
            "status": "exceeded" if self.max_rss_mb > self.threshold_gb * 1024 else "ok"
        }
        try:
            with open(self.log_file, 'a') as f:
                f.write(json.dumps(summary) + '\n')
        except IOError:
            pass

        # Raise error if threshold was exceeded during execution
        if self.max_rss_mb > self.threshold_gb * 1024:
            raise MemoryError(
                f"Memory threshold exceeded during execution: {self.max_rss_mb / 1024:.2f} GB > {self.threshold_gb} GB"
            )

    def wrap_function(self, func: Callable) -> Callable:
        """
        Decorator to wrap a function with memory monitoring.

        Args:
            func: The function to wrap.

        Returns:
            The wrapped function.
        """
        def wrapper(*args, **kwargs):
            with self:
                return func(*args, **kwargs)
        return wrapper


def run_with_memory_monitor(
    func: Callable,
    log_file: Optional[str] = None,
    threshold_gb: float = 6.0,
    interval: float = 1.0
) -> Any:
    """
    Run a function under memory monitoring.

    Args:
        func: The function to execute.
        log_file: Path to the log file.
        threshold_gb: RAM threshold in GB.
        interval: Sampling interval in seconds.

    Returns:
        The return value of the function.

    Raises:
        MemoryError: If memory usage exceeds the threshold.
    """
    monitor = MemoryMonitor(
        log_file=log_file,
        threshold_gb=threshold_gb,
        interval=interval
    )
    return monitor.wrap_function(func)()