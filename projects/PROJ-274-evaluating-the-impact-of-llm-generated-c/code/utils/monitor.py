"""
Active monitoring context manager for logging peak memory and wall-clock time.

This module provides a context manager that tracks resource usage during
execution, specifically peak Resident Set Size (RSS) memory and elapsed
wall-clock time. It is designed to satisfy FR-010 requirements for
resource constraint verification.

Usage:
    with ActiveMonitor() as monitor:
        # ... code to monitor ...
        monitor.log_summary("analysis_phase")

    # Access results
    print(f"Peak Memory: {monitor.peak_memory_mb:.2f} MB")
    print(f"Elapsed Time: {monitor.elapsed_seconds:.2f} seconds")
"""

import os
import time
import logging
import json
from typing import Optional, Dict, Any
from pathlib import Path

try:
    import psutil
except ImportError:
    raise ImportError(
        "The 'psutil' library is required for memory monitoring. "
        "Install it via: pip install psutil"
    )

# Configure logging for the module
logger = logging.getLogger(__name__)
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)


class ActiveMonitor:
    """
    Context manager to monitor peak memory usage and wall-clock time.

    Attributes:
        start_time (float): Timestamp when the monitor started.
        peak_memory_mb (float): Peak Resident Set Size (RSS) in megabytes.
        elapsed_seconds (float): Total wall-clock time in seconds.
        log_path (Optional[Path]): Path to a JSON log file if specified.
        process (psutil.Process): The current process object.
    """

    def __init__(self, log_path: Optional[str] = None, tag: str = "monitor"):
        """
        Initialize the monitor.

        Args:
            log_path: Optional path to a JSON file where results will be appended.
            tag: A string identifier for this monitoring session (e.g., 'analysis', 'generation').
        """
        self.tag = tag
        self.start_time: float = 0.0
        self.peak_memory_mb: float = 0.0
        self.elapsed_seconds: float = 0.0
        self.log_path: Optional[Path] = Path(log_path) if log_path else None
        self.process = psutil.Process(os.getpid())
        self._measurements: list = []

    def __enter__(self) -> 'ActiveMonitor':
        """Start the timer and initialize memory tracking."""
        self.start_time = time.perf_counter()
        # Initial memory capture to establish baseline
        try:
            initial_mem = self.process.memory_info().rss
            self.peak_memory_mb = initial_mem / (1024 * 1024)
        except psutil.NoSuchProcess:
            logger.warning("Process no longer exists during start.")
            self.peak_memory_mb = 0.0
        
        logger.info(f"[{self.tag}] Monitor started.")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Stop the timer and finalize measurements."""
        self.elapsed_seconds = time.perf_counter() - self.start_time
        
        # Final memory check to ensure we caught the peak
        try:
            current_mem = self.process.memory_info().rss
            current_mem_mb = current_mem / (1024 * 1024)
            if current_mem_mb > self.peak_memory_mb:
                self.peak_memory_mb = current_mem_mb
        except psutil.NoSuchProcess:
            logger.warning("Process no longer exists during exit.")

        logger.info(
            f"[{self.tag}] Monitor finished. "
            f"Peak Memory: {self.peak_memory_mb:.2f} MB, "
            f"Elapsed Time: {self.elapsed_seconds:.2f} s"
        )

        # Log to file if path provided
        if self.log_path:
            self._write_log()

    def _write_log(self):
        """Write the current session metrics to the JSON log file."""
        if not self.log_path:
            return

        # Ensure directory exists
        self.log_path.parent.mkdir(parents=True, exist_ok=True)

        data = {
            "tag": self.tag,
            "peak_memory_mb": round(self.peak_memory_mb, 2),
            "elapsed_seconds": round(self.elapsed_seconds, 4),
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S")
        }

        # Append to existing file if it exists
        if self.log_path.exists():
            try:
                with open(self.log_path, 'r') as f:
                    content = f.read().strip()
                    if content:
                        # Handle simple JSON array or just append new line if not array
                        # Simple approach: read as list, append, write back
                        try:
                            records = json.loads(content)
                            if not isinstance(records, list):
                                records = [records]
                            records.append(data)
                        except json.JSONDecodeError:
                            # Fallback if file is malformed, start fresh
                            records = [data]
                    else:
                        records = [data]
            except Exception as e:
                logger.error(f"Error reading log file {self.log_path}: {e}")
                records = [data]
        else:
            records = [data]

        with open(self.log_path, 'w') as f:
            json.dump(records, f, indent=2)

    def check_memory_limit(self, limit_gb: float) -> bool:
        """
        Check if peak memory is within a specified limit.

        Args:
            limit_gb: Maximum allowed memory in Gigabytes.

        Returns:
            True if within limit, False otherwise.
        """
        limit_mb = limit_gb * 1024
        is_ok = self.peak_memory_mb < limit_mb
        if not is_ok:
            logger.error(
                f"[{self.tag}] MEMORY LIMIT EXCEEDED: "
                f"{self.peak_memory_mb:.2f} MB > {limit_mb:.2f} MB"
            )
        return is_ok

    def check_time_limit(self, limit_seconds: float) -> bool:
        """
        Check if elapsed time is within a specified limit.

        Args:
            limit_seconds: Maximum allowed time in seconds.

        Returns:
            True if within limit, False otherwise.
        """
        is_ok = self.elapsed_seconds < limit_seconds
        if not is_ok:
            logger.error(
                f"[{self.tag}] TIME LIMIT EXCEEDED: "
                f"{self.elapsed_seconds:.2f} s > {limit_seconds:.2f} s"
            )
        return is_ok

    def get_report(self) -> Dict[str, Any]:
        """Return a dictionary of the current monitoring results."""
        return {
            "tag": self.tag,
            "peak_memory_mb": self.peak_memory_mb,
            "elapsed_seconds": self.elapsed_seconds
        }


# Convenience function for one-off monitoring without explicit context management
def monitor_execution(func, log_path: Optional[str] = None, tag: str = "func_monitor"):
    """
    Decorator to monitor a function's execution time and memory.

    Args:
        func: The function to wrap.
        log_path: Optional path to log results.
        tag: Identifier for the log entry.

    Returns:
        Wrapped function.
    """
    def wrapper(*args, **kwargs):
        with ActiveMonitor(log_path=log_path, tag=tag) as monitor:
            result = func(*args, **kwargs)
        return result
    return wrapper