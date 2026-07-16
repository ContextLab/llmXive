"""
Resource Monitor Module

Provides a context manager and decorator to enforce configurable memory limits
for research tasks running on constrained CPU-only runners (FR-007).

Features:
- Active memory monitoring via psutil
- Configurable soft/hard limits (default 4GB)
- Logging of resource trends
- Process termination on hard limit violation
"""

import os
import sys
import time
import logging
import threading
from functools import wraps
from typing import Optional, Callable, Union
from pathlib import Path

try:
    import psutil
except ImportError:
    raise ImportError(
        "The 'psutil' library is required for resource monitoring. "
        "Install it via: pip install psutil"
    )

# Configure logging
logger = logging.getLogger(__name__)
if not logger.handlers:
    handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

# Default limit: 4GB (derived from 7GB runner constraint)
DEFAULT_MEMORY_LIMIT_BYTES = 4 * 1024 * 1024 * 1024  # 4 GB


class MemoryLimitExceeded(Exception):
    """Exception raised when memory usage exceeds the hard limit."""
    pass


class ResourceMonitor:
    """
    Context manager and utility class for monitoring and enforcing memory limits.

    Args:
        limit_bytes (int): Memory limit in bytes. Default is 4GB.
        check_interval (float): Interval in seconds between memory checks. Default 0.5s.
        log_file (Optional[str]): Path to log file for resource trends. If None, logs to stdout.
        soft_limit_factor (float): Factor for soft limit warning (0.0-1.0). Default 0.9 (90%).
    """

    def __init__(
        self,
        limit_bytes: int = DEFAULT_MEMORY_LIMIT_BYTES,
        check_interval: float = 0.5,
        log_file: Optional[Union[str, Path]] = None,
        soft_limit_factor: float = 0.9
    ):
        self.limit_bytes = limit_bytes
        self.check_interval = check_interval
        self.soft_limit_bytes = int(limit_bytes * soft_limit_factor)
        self.log_file = Path(log_file) if log_file else None
        
        self._monitor_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._memory_samples: list = []
        self._process = psutil.Process(os.getpid())
        self._start_time: Optional[float] = None

        if self.log_file:
            self.log_file.parent.mkdir(parents=True, exist_ok=True)

    def _get_current_memory(self) -> int:
        """Get current RSS memory usage in bytes."""
        return self._process.memory_info().rss

    def _monitor_loop(self):
        """Background thread loop for monitoring memory usage."""
        while not self._stop_event.is_set():
            current_mem = self._get_current_memory()
            self._memory_samples.append(current_mem)
            
            elapsed = time.time() - self._start_time if self._start_time else 0
            
            # Log trends periodically
            if len(self._memory_samples) % 10 == 0:
                logger.debug(
                    f"Memory Trend: {current_mem / 1024 / 1024:.2f} MB "
                    f"(Limit: {self.limit_bytes / 1024 / 1024:.2f} MB) "
                    f"Elapsed: {elapsed:.2f}s"
                )

            # Check for soft limit warning
            if current_mem > self.soft_limit_bytes:
                logger.warning(
                    f"Soft limit exceeded: {current_mem / 1024 / 1024:.2f} MB "
                    f"({100 * current_mem / self.limit_bytes:.1f}% of limit)"
                )

            # Check for hard limit violation
            if current_mem > self.limit_bytes:
                logger.error(
                    f"HARD LIMIT EXCEEDED: {current_mem / 1024 / 1024:.2f} MB "
                    f"({100 * current_mem / self.limit_bytes:.1f}% of limit). "
                    f"Terminating process."
                )
                # Log final stats
                if self.log_file:
                    self._write_log()
                
                # Kill process forcefully
                os._exit(1)

            time.sleep(self.check_interval)

    def _write_log(self):
        """Write memory trend log to file."""
        if not self.log_file:
            return
        
        with open(self.log_file, 'w') as f:
            f.write("timestamp, memory_mb, percent_limit\n")
            base_time = self._start_time if self._start_time else time.time()
            for i, mem in enumerate(self._memory_samples):
                t = base_time + i * self.check_interval
                f.write(f"{t:.2f}, {mem / 1024 / 1024:.2f}, {100 * mem / self.limit_bytes:.2f}\n")

    def __enter__(self):
        """Start monitoring on context entry."""
        self._start_time = time.time()
        self._memory_samples = []
        self._stop_event.clear()
        
        logger.info(f"ResourceMonitor started. Limit: {self.limit_bytes / 1024 / 1024:.2f} MB")
        
        self._monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self._monitor_thread.start()
        
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Stop monitoring and write final logs on context exit."""
        self._stop_event.set()
        if self._monitor_thread:
            self._monitor_thread.join(timeout=2.0)
        
        elapsed = time.time() - self._start_time if self._start_time else 0
        final_mem = self._get_current_memory()
        
        logger.info(
            f"ResourceMonitor finished. "
            f"Duration: {elapsed:.2f}s, "
            f"Peak Memory: {max(self._memory_samples) / 1024 / 1024:.2f} MB"
        )
        
        if self.log_file:
            self._write_log()
            logger.info(f"Trend log written to: {self.log_file}")
        
        return False  # Do not suppress exceptions

    def get_peak_memory(self) -> int:
        """Get peak memory usage during monitoring."""
        return max(self._memory_samples) if self._memory_samples else self._get_current_memory()

    def get_current_memory(self) -> int:
        """Get current memory usage."""
        return self._get_current_memory()


def resource_monitor(
    limit_bytes: int = DEFAULT_MEMORY_LIMIT_BYTES,
    check_interval: float = 0.5,
    log_file: Optional[str] = None,
    soft_limit_factor: float = 0.9
):
    """
    Decorator to enforce memory limits on a function.

    Args:
        limit_bytes: Memory limit in bytes.
        check_interval: Check interval in seconds.
        log_file: Optional path to log file.
        soft_limit_factor: Factor for soft limit warning.

    Returns:
        Decorated function with memory monitoring.
    """
    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            with ResourceMonitor(
                limit_bytes=limit_bytes,
                check_interval=check_interval,
                log_file=log_file,
                soft_limit_factor=soft_limit_factor
            ):
                return func(*args, **kwargs)
        return wrapper
    return decorator


# Convenience function to get current process memory
def get_process_memory_mb() -> float:
    """Get current process memory usage in MB."""
    process = psutil.Process(os.getpid())
    return process.memory_info().rss / 1024 / 1024
