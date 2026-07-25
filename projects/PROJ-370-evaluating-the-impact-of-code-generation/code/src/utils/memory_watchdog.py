"""
Memory watchdog utility for monitoring process memory usage during inference.

This module provides functionality to monitor the resident set size (RSS) of the
current process. If memory usage exceeds a configurable threshold (default 7GB),
it logs a warning to a dedicated log file and raises a MemoryLimitExceeded exception
to trigger graceful skipping of the current inference task.
"""

import os
import sys
import time
import logging
import threading
from pathlib import Path
from typing import Optional, Callable, Any
from contextlib import contextmanager

# Import project paths from config
from code.config.settings import get_paths, ensure_directories

# Threshold constant (7GB in bytes)
MEMORY_THRESHOLD_BYTES = 7 * 1024 * 1024 * 1024

class MemoryLimitExceeded(Exception):
    """Exception raised when memory usage exceeds the configured threshold."""
    pass

def get_memory_usage_bytes() -> int:
    """
    Get the current Resident Set Size (RSS) of the process in bytes.

    Returns:
        int: Memory usage in bytes.
    """
    try:
        # Read from /proc/self/status on Linux
        with open('/proc/self/status', 'r') as f:
            for line in f:
                if line.startswith('VmRSS:'):
                    # Format: "VmRSS:     12345 kB"
                    parts = line.split()
                    if len(parts) >= 2:
                        return int(parts[1]) * 1024  # Convert kB to bytes
        # Fallback: use resource module if available
        import resource
        usage = resource.getrusage(resource.RUSAGE_SELF)
        return usage.ru_maxrss * 1024  # Convert kB to bytes (Linux)
    except Exception:
        # Fallback to 0 if we can't determine memory usage
        return 0

def check_memory_limit(threshold_bytes: int = MEMORY_THRESHOLD_BYTES) -> bool:
    """
    Check if current memory usage exceeds the threshold.

    Args:
        threshold_bytes: The memory threshold in bytes.

    Returns:
        bool: True if memory usage exceeds threshold, False otherwise.
    """
    current_memory = get_memory_usage_bytes()
    return current_memory > threshold_bytes

def setup_memory_logging(log_dir: Optional[Path] = None) -> logging.Logger:
    """
    Setup a dedicated logger for memory warnings.

    Args:
        log_dir: Directory for log files. Defaults to project logs directory.

    Returns:
        logging.Logger: Configured logger instance.
    """
    if log_dir is None:
        paths = get_paths()
        log_dir = paths.get('logs_dir', Path('logs'))

    ensure_directories([log_dir])
    log_file = log_dir / 'memory_warning.log'

    logger = logging.getLogger('memory_watchdog')
    logger.setLevel(logging.WARNING)

    # Remove existing handlers to avoid duplicates
    logger.handlers = []

    # File handler
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(logging.WARNING)

    # Formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    file_handler.setFormatter(formatter)

    logger.addHandler(file_handler)

    return logger

class MemoryMonitor:
    """
    Context manager and decorator for monitoring memory usage.

    If memory usage exceeds the threshold during execution, it logs a warning
    and raises MemoryLimitExceeded to allow graceful skipping.
    """

    def __init__(
        self,
        threshold_bytes: int = MEMORY_THRESHOLD_BYTES,
        check_interval_seconds: float = 1.0,
        logger: Optional[logging.Logger] = None
    ):
        """
        Initialize the memory monitor.

        Args:
            threshold_bytes: Memory threshold in bytes.
            check_interval_seconds: How often to check memory (seconds).
            logger: Logger instance. If None, creates a default one.
        """
        self.threshold_bytes = threshold_bytes
        self.check_interval_seconds = check_interval_seconds
        self.logger = logger or setup_memory_logging()
        self._stop_event = threading.Event()
        self._monitor_thread: Optional[threading.Thread] = None

    def _monitor_loop(self) -> None:
        """Background thread that periodically checks memory usage."""
        while not self._stop_event.is_set():
            if check_memory_limit(self.threshold_bytes):
                current_memory = get_memory_usage_bytes()
                memory_gb = current_memory / (1024 ** 3)
                threshold_gb = self.threshold_bytes / (1024 ** 3)

                self.logger.warning(
                    f"Memory limit exceeded! Current: {memory_gb:.2f}GB, "
                    f"Threshold: {threshold_gb:.2f}GB. "
                    f"Triggering graceful skip."
                )
                self._stop_event.set()  # Stop monitoring
                raise MemoryLimitExceeded(
                    f"Memory usage {memory_gb:.2f}GB exceeds limit {threshold_gb:.2f}GB"
                )
            time.sleep(self.check_interval_seconds)

    def __enter__(self) -> 'MemoryMonitor':
        """Start the memory monitoring thread."""
        self._stop_event.clear()
        self._monitor_thread = threading.Thread(
            target=self._monitor_loop,
            daemon=True
        )
        self._monitor_thread.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Stop the monitoring thread."""
        self._stop_event.set()
        if self._monitor_thread:
            self._monitor_thread.join(timeout=1.0)

    @staticmethod
    @contextmanager
    def watch(
        threshold_bytes: int = MEMORY_THRESHOLD_BYTES,
        check_interval_seconds: float = 1.0
    ):
        """
        Context manager to wrap a block of code with memory monitoring.

        Args:
            threshold_bytes: Memory threshold in bytes.
            check_interval_seconds: How often to check memory (seconds).

        Raises:
            MemoryLimitExceeded: If memory usage exceeds threshold.

        Example:
            with MemoryMonitor.watch():
                # Code that might use too much memory
                heavy_computation()
        """
        logger = setup_memory_logging()
        monitor = MemoryMonitor(
            threshold_bytes=threshold_bytes,
            check_interval_seconds=check_interval_seconds,
            logger=logger
        )
        with monitor:
            yield

def enforce_memory_limit(
    func: Callable[..., Any]
) -> Callable[..., Any]:
    """
    Decorator to enforce memory limits on a function.

    If memory usage exceeds the threshold during function execution,
    it logs a warning and raises MemoryLimitExceeded.

    Args:
        func: The function to wrap.

    Returns:
        The wrapped function.
    """
    def wrapper(*args, **kwargs):
        logger = setup_memory_logging()
        logger.info(f"Starting memory-monitored execution of {func.__name__}")

        try:
            with MemoryMonitor.watch():
                return func(*args, **kwargs)
        except MemoryLimitExceeded as e:
            logger.error(f"Memory limit exceeded in {func.__name__}: {e}")
            raise

    return wrapper

def main() -> None:
    """
    Main function to demonstrate memory monitoring.

    This function runs a simple test to verify the memory monitoring works.
    """
    logger = setup_memory_logging()
    logger.info("Memory watchdog initialized.")
    logger.info(f"Threshold: {MEMORY_THRESHOLD_BYTES / (1024**3):.2f}GB")

    # Example usage
    try:
        with MemoryMonitor.watch():
            logger.info("Monitoring memory usage...")
            time.sleep(2)
            # Simulate memory check
            current_mem = get_memory_usage_bytes()
            logger.info(f"Current memory: {current_mem / (1024**3):.2f}GB")
    except MemoryLimitExceeded as e:
        logger.error(f"Caught memory limit exception: {e}")

if __name__ == "__main__":
    main()
