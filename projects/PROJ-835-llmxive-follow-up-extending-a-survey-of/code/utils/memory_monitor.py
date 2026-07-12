"""
Memory monitoring utilities for the LlmXive pipeline.
Tracks peak RAM usage and enforces hard memory limits to prevent OOM errors.
"""
import os
import gc
import psutil
import threading
import time
from typing import Optional, Callable, Any
from contextlib import contextmanager

# Global state for memory tracking
_process = psutil.Process()
_peak_memory_mb: float = 0.0
_memory_limit_mb: Optional[float] = None
_lock = threading.Lock()
_watcher_thread: Optional[threading.Thread] = None
_stop_watcher = threading.Event()


def set_memory_limit(limit_gb: float) -> None:
    """
    Set the global memory limit in GB.
    
    Args:
        limit_gb: Maximum allowed memory usage in gigabytes.
    """
    global _memory_limit_mb
    with _lock:
        _memory_limit_mb = limit_gb * 1024  # Convert GB to MB


def get_memory_limit_gb() -> Optional[float]:
    """
    Get the current memory limit in GB.
    
    Returns:
        The limit in GB, or None if not set.
    """
    with _lock:
        if _memory_limit_mb is None:
            return None
        return _memory_limit_mb / 1024.0


def get_current_memory_mb() -> float:
    """
    Get the current RSS (Resident Set Size) memory usage of the process in MB.
    
    Returns:
        Current memory usage in MB.
    """
    return _process.memory_info().rss / (1024 * 1024)


def get_peak_memory_mb() -> float:
    """
    Get the peak memory usage recorded so far in MB.
    
    Returns:
        Peak memory usage in MB.
    """
    with _lock:
        return _peak_memory_mb


def update_peak_memory() -> float:
    """
    Update the global peak memory tracker with the current usage.
    
    Returns:
        The updated peak memory value in MB.
    """
    current = get_current_memory_mb()
    with _lock:
        global _peak_memory_mb
        if current > _peak_memory_mb:
            _peak_memory_mb = current
    return _peak_memory_mb


def check_memory_limit() -> bool:
    """
    Check if the current memory usage exceeds the set limit.
    
    Returns:
        True if within limits, False if limit exceeded.
        
    Raises:
        MemoryError: If the limit is exceeded.
    """
    if _memory_limit_mb is None:
        return True
    
    current = get_current_memory_mb()
    update_peak_memory()
    
    if current > _memory_limit_mb:
        raise MemoryError(
            f"Memory limit exceeded: {current:.2f} MB > {_memory_limit_mb:.2f} MB"
        )
    return True


def force_gc() -> None:
    """
    Force garbage collection and update peak memory tracking.
    """
    gc.collect()
    update_peak_memory()


def _memory_watcher_loop(interval: float = 1.0) -> None:
    """
    Background thread loop to periodically update peak memory.
    
    Args:
        interval: Check interval in seconds.
    """
    while not _stop_watcher.is_set():
        update_peak_memory()
        _stop_watcher.wait(interval)


def start_memory_watcher(interval: float = 1.0) -> None:
    """
    Start a background thread to continuously monitor memory usage.
    
    Args:
        interval: How often to check memory in seconds.
    """
    global _watcher_thread
    if _watcher_thread is not None and _watcher_thread.is_alive():
        return
    
    _stop_watcher.clear()
    _watcher_thread = threading.Thread(
        target=_memory_watcher_loop, 
        args=(interval,), 
        daemon=True
    )
    _watcher_thread.start()


def stop_memory_watcher() -> None:
    """
    Stop the background memory watcher thread.
    """
    global _watcher_thread
    _stop_watcher.set()
    if _watcher_thread is not None:
        _watcher_thread.join(timeout=2.0)
        _watcher_thread = None


@contextmanager
def memory_limit_context(limit_gb: float):
    """
    Context manager to enforce a temporary memory limit.
    
    Args:
        limit_gb: Temporary limit in GB.
        
    Yields:
        None
        
    Raises:
        MemoryError: If memory usage exceeds the limit.
    """
    old_limit = get_memory_limit_gb()
    set_memory_limit(limit_gb)
    try:
        yield
        check_memory_limit()
    finally:
        set_memory_limit(old_limit if old_limit is not None else 0)


class MemoryWatcher:
    """
    Class-based interface for memory monitoring.
    """
    def __init__(self, limit_gb: float, check_interval: float = 1.0):
        """
        Initialize the memory watcher.
        
        Args:
            limit_gb: Memory limit in GB.
            check_interval: Interval for background checks in seconds.
        """
        self.limit_gb = limit_gb
        self.check_interval = check_interval
        self._thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
    
    def start(self) -> None:
        """Start the background monitoring thread."""
        if self._thread and self._thread.is_alive():
            return
        
        set_memory_limit(self.limit_gb)
        self._stop_event.clear()
        self._thread = threading.Thread(
            target=self._watch_loop,
            daemon=True
        )
        self._thread.start()
    
    def _watch_loop(self) -> None:
        while not self._stop_event.is_set():
            try:
                check_memory_limit()
            except MemoryError:
                # Force GC and re-check
                force_gc()
                try:
                    check_memory_limit()
                except MemoryError:
                    # If still exceeded, raise immediately
                    raise
            self._stop_event.wait(self.check_interval)
    
    def stop(self) -> None:
        """Stop the background monitoring thread."""
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=2.0)
            self._thread = None
    
    def get_peak(self) -> float:
        """Get current peak memory in MB."""
        return get_peak_memory_mb()
    
    def get_current(self) -> float:
        """Get current memory in MB."""
        return get_current_memory_mb()


def enforce_limit(limit_gb: float, check_interval: float = 1.0) -> MemoryWatcher:
    """
    Convenience function to start a memory watcher with a specific limit.
    
    Args:
        limit_gb: Memory limit in GB.
        check_interval: Check interval in seconds.
        
    Returns:
        A started MemoryWatcher instance.
    """
    watcher = MemoryWatcher(limit_gb, check_interval)
    watcher.start()
    return watcher