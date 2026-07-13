"""
Memory monitoring utility using psutil.

Provides functions to track peak memory usage during script execution,
specifically for monitoring model training tasks.
"""
import psutil
import os
import atexit
import logging
from typing import Optional

# Initialize process and tracking variables
_process = psutil.Process(os.getpid())
_peak_memory: int = 0  # In bytes
_logger: Optional[logging.Logger] = None

def _get_logger() -> logging.Logger:
    """Get or create the module logger."""
    global _logger
    if _logger is None:
        _logger = logging.getLogger(__name__)
        if not _logger.handlers:
            _logger.setLevel(logging.INFO)
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            _logger.addHandler(handler)
    return _logger

def update_peak_memory():
    """Update the recorded peak memory usage."""
    global _peak_memory
    try:
        current_memory = _process.memory_info().rss
        if current_memory > _peak_memory:
            _peak_memory = current_memory
    except Exception as e:
        _get_logger().warning(f"Failed to update memory usage: {e}")

def get_peak_memory_mb() -> float:
    """Return the peak memory usage in MB."""
    return _peak_memory / (1024 * 1024)

def reset_peak_memory():
    """Reset the peak memory counter."""
    global _peak_memory
    _peak_memory = 0

def log_peak_memory(message: str = "Peak memory usage") -> None:
    """Log the current peak memory usage in MB."""
    peak_mb = get_peak_memory_mb()
    logger = _get_logger()
    logger.info(f"{message}: {peak_mb:.2f} MB")

def monitor_memory_interval(interval_seconds: float = 5.0) -> None:
    """
    Start a background thread to periodically update peak memory.
    
    Args:
        interval_seconds: Time between updates in seconds.
    """
    import threading
    import time

    def _monitor_loop():
        while True:
            update_peak_memory()
            time.sleep(interval_seconds)

    thread = threading.Thread(target=_monitor_loop, daemon=True)
    thread.start()
    _get_logger().info(f"Started memory monitor thread (interval: {interval_seconds}s)")

# Register update on exit to ensure final check
atexit.register(update_peak_memory)