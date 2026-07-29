"""
Memory monitoring utilities for enforcing hard abort on memory limit violations (FR-005).
Tracks peak RSS via /proc/self/status and provides enforcement mechanisms.
"""
import os
import sys
import time
import threading
from typing import Optional, Callable, Any
from pathlib import Path

from utils.exceptions import DataIntegrityError


class MemoryLimitExceeded(RuntimeError):
    """Raised when memory usage exceeds the configured hard limit."""
    pass


def get_current_rss_kb() -> int:
    """
    Get current Resident Set Size (RSS) in kilobytes from /proc/self/status.
    
    Returns:
        Current RSS in KB.
        
    Raises:
        RuntimeError: If /proc/self/status is not accessible or parsing fails.
    """
    try:
        with open('/proc/self/status', 'r') as f:
            for line in f:
                if line.startswith('VmRSS:'):
                    # Format: "VmRSS:    12345 kB"
                    parts = line.split()
                    if len(parts) >= 2:
                        return int(parts[1])
        # Fallback if VmRSS not found
        return 0
    except (IOError, ValueError) as e:
        raise RuntimeError(f"Failed to read memory status: {e}")


def get_peak_rss_kb() -> int:
    """
    Get peak RSS (VmPeak) in kilobytes from /proc/self/status.
    
    Returns:
        Peak RSS in KB.
        
    Raises:
        RuntimeError: If /proc/self/status is not accessible or parsing fails.
    """
    try:
        with open('/proc/self/status', 'r') as f:
            for line in f:
                if line.startswith('VmPeak:'):
                    # Format: "VmPeak:    12345 kB"
                    parts = line.split()
                    if len(parts) >= 2:
                        return int(parts[1])
        # Fallback if VmPeak not found
        return get_current_rss_kb()
    except (IOError, ValueError) as e:
        raise RuntimeError(f"Failed to read peak memory status: {e}")


class MemoryMonitor:
    """
    Monitors memory usage in a background thread and tracks peak RSS.
    Enforces hard abort if memory limit is exceeded.
    """
    
    def __init__(self, limit_mb: float, check_interval_seconds: float = 0.1):
        """
        Initialize the memory monitor.
        
        Args:
            limit_mb: Hard memory limit in megabytes.
            check_interval_seconds: How often to check memory usage.
        """
        self.limit_kb = int(limit_mb * 1024)
        self.check_interval = check_interval_seconds
        self._stop_event = threading.Event()
        self._peak_rss_kb = 0
        self._monitor_thread: Optional[threading.Thread] = None
        self._last_check_time = 0.0
    
    def _monitor_loop(self):
        """Background loop that checks memory usage and enforces limits."""
        while not self._stop_event.is_set():
            try:
                current_rss = get_current_rss_kb()
                if current_rss > self._peak_rss_kb:
                    self._peak_rss_kb = current_rss
                
                # Hard abort if limit exceeded
                if current_rss > self.limit_kb:
                    self._stop_event.set()
                    msg = (
                        f"Memory limit exceeded: {current_rss / 1024:.2f} MB "
                        f"(limit: {self.limit_kb / 1024:.2f} MB). "
                        f"Peak RSS: {self._peak_rss_kb / 1024:.2f} MB. "
                        "Aborting execution as per FR-005."
                    )
                    # Log to stderr before aborting
                    sys.stderr.write(f"ERROR: {msg}\n")
                    sys.stderr.flush()
                    raise MemoryLimitExceeded(msg)
                
            except Exception as e:
                # Re-raise if it's our custom exception, otherwise log and continue
                if isinstance(e, MemoryLimitExceeded):
                    raise
                # Log other errors but continue monitoring
                sys.stderr.write(f"Warning: Memory check failed: {e}\n")
            
            self._stop_event.wait(self.check_interval)
    
    def start(self):
        """Start the background monitoring thread."""
        if self._monitor_thread is not None and self._monitor_thread.is_alive():
            return  # Already running
        
        self._stop_event.clear()
        self._peak_rss_kb = get_current_rss_kb()
        self._monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self._monitor_thread.start()
    
    def stop(self):
        """Stop the monitoring thread."""
        if self._monitor_thread is not None and self._monitor_thread.is_alive():
            self._stop_event.set()
            self._monitor_thread.join(timeout=1.0)
            self._monitor_thread = None
    
    def get_peak_rss(self) -> int:
        """
        Get the peak RSS observed since monitoring started.
        
        Returns:
            Peak RSS in KB.
        """
        # Update peak with current value if not monitoring
        if self._monitor_thread is None or not self._monitor_thread.is_alive():
            current = get_current_rss_kb()
            if current > self._peak_rss_kb:
                self._peak_rss_kb = current
        return self._peak_rss_kb
    
    def get_peak_rss_mb(self) -> float:
        """Get peak RSS in megabytes."""
        return self.get_peak_rss() / 1024.0


def enforce_memory_limit(limit_mb: float, action: Optional[Callable[[], None]] = None):
    """
    Context manager to enforce memory limits during a code block.
    
    Args:
        limit_mb: Hard memory limit in megabytes.
        action: Optional cleanup function to call before aborting.
        
    Raises:
        MemoryLimitExceeded: If memory limit is exceeded.
    """
    monitor = MemoryMonitor(limit_mb=limit_mb)
    monitor.start()
    try:
        yield monitor
    except MemoryLimitExceeded:
        if action:
            try:
                action()
            except Exception:
                pass  # Ignore cleanup errors during abort
        raise
    finally:
        monitor.stop()


# Generator version of the context manager since we can't use @contextmanager
# with a generator function directly in the type hints, we implement it manually
class MemoryLimitEnforcer:
    """Context manager for enforcing memory limits."""
    
    def __init__(self, limit_mb: float, on_abort: Optional[Callable[[], None]] = None):
        self.limit_mb = limit_mb
        self.on_abort = on_abort
        self.monitor: Optional[MemoryMonitor] = None
    
    def __enter__(self):
        self.monitor = MemoryMonitor(limit_mb=self.limit_mb)
        self.monitor.start()
        return self.monitor
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.monitor:
            self.monitor.stop()
        # Don't suppress MemoryLimitExceeded
        if exc_type is MemoryLimitExceeded:
            if self.on_abort:
                try:
                    self.on_abort()
                except Exception:
                    pass
        return False  # Don't suppress exceptions


def get_peak_rss() -> int:
    """
    Convenience function to get peak RSS in KB.
    
    Returns:
        Peak RSS in KB.
    """
    return get_peak_rss_kb()