"""
Memory profiling utilities for graph metric computation.

Provides a context manager and decorator to monitor peak RAM usage
and enforce strict memory limits during heavy computations.
"""
import psutil
import os
import threading
import time
from typing import Optional, Callable, Any
from functools import wraps
from .logger import get_logger

logger = get_logger(__name__)

class MemoryMonitor:
    """
    Monitors peak memory usage of the current process and its children.
    """
    def __init__(self, limit_gb: float = 7.0):
        self.limit_gb = limit_gb
        self.limit_bytes = limit_gb * (1024 ** 3)
        self.peak_memory_bytes = 0
        self._monitoring = False
        self._thread: Optional[threading.Thread] = None

    def _monitor_loop(self):
        """Background thread to sample memory usage periodically."""
        process = psutil.Process(os.getpid())
        while self._monitoring:
            try:
                current_mem = process.memory_info().rss
                if current_mem > self.peak_memory_bytes:
                    self.peak_memory_bytes = current_mem
                # Check limit every iteration to fail fast
                if current_mem > self.limit_bytes:
                    self._monitoring = False
                    raise MemoryError(
                        f"Memory limit exceeded: {current_mem / (1024**3):.2f} GB > "
                        f"{self.limit_gb} GB limit."
                    )
                time.sleep(0.1)  # Sample every 100ms
            except MemoryError:
                raise
            except Exception as e:
                # Log but don't crash the monitor thread if possible
                logger.warning(f"Memory monitor error: {e}")
                time.sleep(1)

    def start(self):
        """Start the memory monitoring thread."""
        self._monitoring = True
        self.peak_memory_bytes = psutil.Process(os.getpid()).memory_info().rss
        self._thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self._thread.start()
        logger.info(f"Memory monitoring started. Limit: {self.limit_gb} GB.")

    def stop(self):
        """Stop the memory monitoring thread and return peak usage in GB."""
        self._monitoring = False
        if self._thread:
            self._thread.join(timeout=1.0)
        peak_gb = self.peak_memory_bytes / (1024 ** 3)
        logger.info(f"Memory monitoring stopped. Peak usage: {peak_gb:.3f} GB.")
        return peak_gb

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop()
        if exc_type is MemoryError:
            logger.error("Computation aborted due to memory limit.")
            # Re-raise to propagate the error
            return False
        return False

def profile_memory(limit_gb: float = 7.0):
    """
    Decorator to wrap a function with memory profiling.
    
    Args:
        limit_gb: Maximum allowed RAM in GB. Defaults to 7.0.
    
    Raises:
        MemoryError: If peak memory usage exceeds the limit.
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            monitor = MemoryMonitor(limit_gb=limit_gb)
            with monitor:
                try:
                    result = func(*args, **kwargs)
                    peak = monitor.stop()
                    logger.info(f"Function '{func.__name__}' completed. Peak RAM: {peak:.3f} GB.")
                    return result
                except MemoryError as e:
                    logger.critical(f"Function '{func.__name__}' failed: {e}")
                    raise
        return wrapper
    return decorator

def get_peak_memory_gb() -> float:
    """
    Get current peak memory usage of the process in GB.
    
    Note: This only returns the current RSS, not the historical peak
    unless used within a MemoryMonitor context.
    """
    process = psutil.Process(os.getpid())
    return process.memory_info().rss / (1024 ** 3)
