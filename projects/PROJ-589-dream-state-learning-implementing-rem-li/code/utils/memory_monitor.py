"""
Memory monitoring utilities for the Dream-State Learning pipeline.

This module provides functionality to track peak RSS (Resident Set Size) memory
usage via /proc/self/status and enforce hard abort on memory limit violations
as required by FR-005.
"""
import os
import sys
import time
from typing import Optional, Callable, Any
from pathlib import Path

# Import custom exception from exceptions module
from utils.exceptions import DataIntegrityError  # Reusing pattern, though ideally a specific MemoryLimitExceeded would be defined


class MemoryLimitExceeded(RuntimeError):
    """Exception raised when memory usage exceeds the configured limit."""
    pass


class MemoryMonitor:
    """
    Monitors peak RSS memory usage via /proc/self/status and enforces hard abort.

    This class tracks the maximum memory usage observed since instantiation and
    provides methods to check current usage against a configured limit.
    """

    def __init__(self, max_memory_gb: float, logger: Optional[Callable] = None):
        """
        Initialize the memory monitor.

        Args:
            max_memory_gb: Maximum allowed memory in gigabytes.
            logger: Optional logger function that accepts (level, message).
        """
        self.max_memory_bytes = max_memory_gb * (1024 ** 3)
        self.peak_rss_bytes = 0
        self.logger = logger
        self._check_interval = 0.1  # seconds between checks when active
        self._is_monitoring = False
        self._monitor_thread: Optional[Any] = None
        self._stop_monitoring = False

        if self.logger is None:
            # Fallback to basic print if no logger provided
            self.logger = lambda level, msg: print(f"[{level}] {msg}")

    def _read_current_rss(self) -> int:
        """
        Read current RSS from /proc/self/status.

        Returns:
            Current RSS in bytes.

        Raises:
            RuntimeError: If /proc/self/status is not accessible (non-Linux).
        """
        if sys.platform != "linux" and sys.platform != "linux2":
            raise RuntimeError("MemoryMonitor is Linux-specific and uses /proc/self/status")

        try:
            with open("/proc/self/status", "r") as f:
                for line in f:
                    if line.startswith("VmRSS:"):
                        # Format: "VmRSS:     12345 kB"
                        parts = line.split()
                        if len(parts) >= 2:
                            rss_kb = int(parts[1])
                            return rss_kb * 1024
            # Fallback if VmRSS not found
            return 0
        except FileNotFoundError:
            raise RuntimeError("Could not read /proc/self/status")
        except ValueError:
            return 0

    def _monitor_loop(self) -> None:
        """Background monitoring loop."""
        while not self._stop_monitoring:
            current_rss = self._read_current_rss()
            if current_rss > self.peak_rss_bytes:
                self.peak_rss_bytes = current_rss

            # Check limit
            if current_rss > self.max_memory_bytes:
                self._log("ERROR", f"Memory limit exceeded: {current_rss / (1024**3):.2f}GB > {self.max_memory_bytes / (1024**3):.2f}GB")
                self._log("ERROR", "Initiating hard abort as per FR-005")
                self._stop_monitoring = True
                self._safe_abort()

            time.sleep(self._check_interval)

    def _log(self, level: str, message: str) -> None:
        """Log a message if logger is available."""
        if self.logger:
            self.logger(level, message)

    def _safe_abort(self) -> None:
        """
        Perform a hard abort, saving checkpoint if possible.

        This method attempts to save a minimal checkpoint before exiting.
        """
        try:
            checkpoint_dir = Path("data/checkpoints")
            checkpoint_dir.mkdir(parents=True, exist_ok=True)
            checkpoint_path = checkpoint_dir / f"oom_abort_{int(time.time())}.json"
            
            # Write minimal checkpoint info
            checkpoint_data = {
                "abort_reason": "MemoryLimitExceeded",
                "peak_rss_gb": self.peak_rss_bytes / (1024**3),
                "limit_gb": self.max_memory_bytes / (1024**3),
                "timestamp": time.time()
            }
            
            import json
            with open(checkpoint_path, "w") as f:
                json.dump(checkpoint_data, f, indent=2)
            
            self._log("INFO", f"Checkpoint saved to {checkpoint_path}")
        except Exception as e:
            self._log("ERROR", f"Failed to save checkpoint: {e}")

        # Force exit
        self._log("CRITICAL", "Hard abort triggered by memory limit")
        os._exit(1)

    def start(self) -> None:
        """Start the background memory monitoring thread."""
        import threading
        self._stop_monitoring = False
        self._is_monitoring = True
        self._monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self._monitor_thread.start()
        self._log("INFO", f"Memory monitoring started (limit: {self.max_memory_bytes / (1024**3):.2f}GB)")

    def stop(self) -> None:
        """Stop the background memory monitoring thread."""
        if self._is_monitoring:
            self._stop_monitoring = True
            if self._monitor_thread:
                self._monitor_thread.join(timeout=1.0)
            self._is_monitoring = False
            self._log("INFO", f"Memory monitoring stopped. Peak RSS: {self.peak_rss_bytes / (1024**3):.2f}GB")

    def get_peak_rss_gb(self) -> float:
        """Get the peak RSS observed so far in gigabytes."""
        return self.peak_rss_bytes / (1024**3)

    def get_current_rss_gb(self) -> float:
        """Get the current RSS in gigabytes."""
        return self._read_current_rss() / (1024**3)

    def check_limit(self) -> None:
        """
        Check current memory usage against limit.

        Raises:
            MemoryLimitExceeded: If current usage exceeds the limit.
        """
        current_rss = self._read_current_rss()
        if current_rss > self.peak_rss_bytes:
            self.peak_rss_bytes = current_rss

        if current_rss > self.max_memory_bytes:
            self._log("ERROR", f"Memory limit exceeded: {current_rss / (1024**3):.2f}GB > {self.max_memory_bytes / (1024**3):.2f}GB")
            self._safe_abort()
            # Should not reach here due to _safe_abort calling os._exit
            raise MemoryLimitExceeded(f"Memory limit exceeded: {current_rss / (1024**3):.2f}GB > {self.max_memory_bytes / (1024**3):.2f}GB")


def get_peak_rss() -> float:
    """
    Get the current peak RSS memory usage in gigabytes.

    Returns:
        Current peak RSS in GB.

    Raises:
        RuntimeError: If not on Linux.
    """
    if sys.platform != "linux" and sys.platform != "linux2":
        raise RuntimeError("get_peak_rss is Linux-specific and uses /proc/self/status")

    try:
        with open("/proc/self/status", "r") as f:
            for line in f:
                if line.startswith("VmRSS:"):
                    parts = line.split()
                    if len(parts) >= 2:
                        rss_kb = int(parts[1])
                        return rss_kb * 1024 / (1024 ** 3)
        return 0.0
    except FileNotFoundError:
        raise RuntimeError("Could not read /proc/self/status")
    except ValueError:
        return 0.0


def enforce_memory_limit(max_memory_gb: float, logger: Optional[Callable] = None) -> MemoryMonitor:
    """
    Create and start a memory monitor that enforces a hard abort on limit violation.

    Args:
        max_memory_gb: Maximum allowed memory in gigabytes.
        logger: Optional logger function.

    Returns:
        Started MemoryMonitor instance.
    """
    monitor = MemoryMonitor(max_memory_gb, logger)
    monitor.start()
    return monitor
