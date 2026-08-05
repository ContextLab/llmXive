import os
import sys
import time
import threading
from typing import Optional, Callable, Any
from pathlib import Path

class MemoryLimitExceeded(Exception):
    """Raised when memory usage exceeds the configured limit."""
    pass

def get_current_rss_kb() -> int:
    """Get current RSS memory usage in KB from /proc/self/status."""
    try:
        with open('/proc/self/status', 'r') as f:
            for line in f:
                if line.startswith('VmRSS:'):
                    return int(line.split()[1])
        return 0
    except (FileNotFoundError, ValueError, IndexError):
        # Fallback for non-Linux systems (estimate or return 0)
        # In production, this should ideally raise or log a warning
        return 0

def get_peak_rss_kb() -> int:
    """Get peak RSS memory usage in KB from /proc/self/status."""
    try:
        with open('/proc/self/status', 'r') as f:
            for line in f:
                if line.startswith('VmPeak:'): # Note: VmPeak is virtual, VmHWM is high watermark
                    # VmHWM is the high watermark of resident set size
                    pass
            # VmHWM is more accurate for peak RSS
            for line in f:
                if line.startswith('VmHWM:'):
                    return int(line.split()[1])
        return 0
    except (FileNotFoundError, ValueError, IndexError):
        return 0

def get_peak_rss() -> int:
    """Alias for get_peak_rss_kb for compatibility."""
    return get_peak_rss_kb()

class MemoryMonitor:
    """Monitors memory usage and enforces limits."""
    def __init__(self, config: Optional[dict] = None):
        self.config = config or {}
        self.limit_kb = self.config.get('memory_limit_kb', 7 * 1024 * 1024) # Default 7GB
        self.check_interval = self.config.get('memory_check_interval_sec', 1.0)
        self._stop_thread = threading.Event()
        self._thread = None

    def check_memory(self) -> dict:
        """Check current memory usage against limit."""
        current_kb = get_current_rss_kb()
        exceeded = current_kb > self.limit_kb
        return {
            'exceeded': exceeded,
            'current_kb': current_kb,
            'limit_kb': self.limit_kb
        }

    def start_monitoring(self, callback: Optional[Callable] = None):
        """Start a background thread to monitor memory."""
        if self._thread and self._thread.is_alive():
            return

        def monitor_loop():
            while not self._stop_thread.is_set():
                status = self.check_memory()
                if status['exceeded']:
                    if callback:
                        callback(status)
                    else:
                        # Default behavior: raise exception
                        raise MemoryLimitExceeded(
                            f"Memory limit exceeded: {status['current_kb']} KB > {status['limit_kb']} KB"
                        )
                time.sleep(self.check_interval)

        self._thread = threading.Thread(target=monitor_loop, daemon=True)
        self._thread.start()

    def stop_monitoring(self):
        """Stop the background monitoring thread."""
        self._stop_thread.set()
        if self._thread:
            self._thread.join(timeout=2.0)

def enforce_memory_limit(limit_kb: int):
    """Convenience function to check memory and raise if exceeded."""
    current = get_current_rss_kb()
    if current > limit_kb:
        raise MemoryLimitExceeded(
            f"Memory limit exceeded: {current} KB > {limit_kb} KB"
        )

class MemoryLimitEnforcer:
    """Context manager for enforcing memory limits."""
    def __init__(self, limit_kb: int):
        self.limit_kb = limit_kb

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        return False

    def check(self):
        enforce_memory_limit(self.limit_kb)
