import os
import gc
import time
import threading
from typing import Optional, Callable, Dict, Any, List
from contextlib import contextmanager

class MemoryMonitor:
    """Monitor memory usage of the process."""
    
    def __init__(self, limit_mb: Optional[float] = None):
        self.limit_mb = limit_mb
        self.history: List[Dict[str, Any]] = []
        self._thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
    
    def get_current_usage_mb(self) -> float:
        """Get current memory usage in MB."""
        try:
            # Try to get RSS from /proc on Linux
            if os.path.exists('/proc/self/status'):
                with open('/proc/self/status', 'r') as f:
                    for line in f:
                        if line.startswith('VmRSS:'):
                            return int(line.split()[1]) / 1024.0
            # Fallback to resource if available (Unix)
            import resource
            return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024.0
        except Exception:
            return 0.0
    
    def check_memory_usage(self) -> bool:
        """Check if memory usage is within limits."""
        if self.limit_mb is None:
            return True
        current = self.get_current_usage_mb()
        if current > self.limit_mb:
            return False
        return True
    
    def enforce_memory_limit(self) -> None:
        """Raise an error if memory limit is exceeded."""
        if not self.check_memory_usage():
            current = self.get_current_usage_mb()
            raise MemoryError(f"Memory limit exceeded: {current:.2f} MB > {self.limit_mb:.2f} MB")
    
    def start_monitoring(self, interval: float = 1.0) -> None:
        """Start background monitoring thread."""
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._monitor_loop, args=(interval,), daemon=True)
        self._thread.start()
    
    def _monitor_loop(self, interval: float) -> None:
        while not self._stop_event.is_set():
            usage = self.get_current_usage_mb()
            self.history.append({"timestamp": time.time(), "usage_mb": usage})
            if self.limit_mb and usage > self.limit_mb:
                self._stop_event.set()
            time.sleep(interval)
    
    def stop_monitoring(self) -> None:
        """Stop the monitoring thread."""
        if self._thread:
            self._stop_event.set()
            self._thread.join(timeout=2.0)
            self._thread = None

@contextmanager
def monitor_memory(limit_mb: Optional[float] = None):
    """Context manager to monitor memory usage."""
    monitor = MemoryMonitor(limit_mb)
    try:
        yield monitor
    finally:
        monitor.stop_monitoring()

def check_memory_usage() -> bool:
    """Global check for memory usage (no limit)."""
    monitor = MemoryMonitor()
    return monitor.check_memory_usage()

def enforce_memory_limit(limit_mb: float) -> None:
    """Global enforcement of memory limit."""
    monitor = MemoryMonitor(limit_mb)
    monitor.enforce_memory_limit()
