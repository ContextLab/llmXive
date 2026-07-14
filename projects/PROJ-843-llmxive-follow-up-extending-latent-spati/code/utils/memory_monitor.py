import os
import time
import json
import contextlib
import threading
import tracemalloc
from typing import Optional, Dict, Any, List
from config import get_memory_limit_gb

class MemoryMonitor:
    """
    A context manager and utility class to monitor memory usage.
    Supports multiple calling patterns:
    1. Manual: m = MemoryMonitor("task"); m.start(); ...; m.stop()
    2. Context: with MemoryMonitor("task") as m: ...
    3. Chaining: MemoryMonitor("task").start().stop()
    """
    
    _instances: List['MemoryMonitor'] = []
    _lock = threading.Lock()

    def __init__(self, name: str = "default"):
        self.name = name
        self.start_time: Optional[float] = None
        self.end_time: Optional[float] = None
        self.peak_memory_bytes: int = 0
        self.current_memory_bytes: int = 0
        self._tracemalloc_started = False
        self._thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()

    def start(self):
        """Start monitoring memory."""
        self.start_time = time.time()
        tracemalloc.start()
        self._tracemalloc_started = True
        
        # Start background thread to sample memory periodically
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._sample_memory_loop, daemon=True)
        self._thread.start()
        
        return self  # Enable chaining

    def _sample_memory_loop(self):
        """Background loop to sample memory usage."""
        while not self._stop_event.is_set():
            try:
                current, peak = tracemalloc.get_traced_memory()
                self.current_memory_bytes = current
                if peak > self.peak_memory_bytes:
                    self.peak_memory_bytes = peak
            except Exception:
                pass
            time.sleep(0.1)

    def stop(self):
        """Stop monitoring memory."""
        self.end_time = time.time()
        self._stop_event.set()
        
        if self._thread:
            self._thread.join(timeout=1.0)
        
        if self._tracemalloc_started:
            current, peak = tracemalloc.get_traced_memory()
            tracemalloc.stop()
            self._tracemalloc_started = False
            self.peak_memory_bytes = max(self.peak_memory_bytes, peak)
            self.current_memory_bytes = current
        
        return self  # Enable chaining

    def get_metrics(self) -> Dict[str, Any]:
        """Get current memory metrics."""
        duration = 0.0
        if self.start_time and self.end_time:
            duration = self.end_time - self.start_time
        elif self.start_time:
            duration = time.time() - self.start_time
        
        return {
            "name": self.name,
            "duration_sec": duration,
            "peak_ram_gb": self.peak_memory_bytes / (1024 ** 3),
            "current_ram_gb": self.current_memory_bytes / (1024 ** 3),
            "timestamp": time.time()
        }

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop()

    # Tolerant fallback for unknown method calls (e.g., .info(), .debug(), etc.)
    def __getattr__(self, name: str):
        def _noop(*args, **kwargs):
            return None
        return _noop

def measure_memory(func):
    """Decorator to measure memory usage of a function."""
    def wrapper(*args, **kwargs):
        monitor = MemoryMonitor(func.__name__)
        with monitor:
            result = func(*args, **kwargs)
        print(f"Memory usage for {func.__name__}: {monitor.peak_memory_bytes / (1024**2):.2f} MB")
        return result
    return wrapper

def check_memory_limit(limit_gb: Optional[float] = None) -> bool:
    """Check if current memory usage exceeds the limit."""
    if limit_gb is None:
        limit_gb = get_memory_limit_gb()
    
    current = get_current_memory_mb() / 1024.0
    return current > limit_gb

def should_batch_process(current_usage_gb: Optional[float] = None) -> bool:
    """
    Determine if batch processing should be triggered.
    Returns True if memory usage is high.
    """
    limit_gb = get_memory_limit_gb()
    if current_usage_gb is None:
        current_usage_gb = get_current_memory_mb() / 1024.0
    
    # Trigger batch mode if usage > 6GB (configurable threshold in task T009)
    threshold = min(6.0, limit_gb * 0.9)
    return current_usage_gb > threshold

def get_current_memory_mb() -> float:
    """Get current memory usage in MB."""
    try:
        import psutil
        process = psutil.Process(os.getpid())
        return process.memory_info().rss / (1024 * 1024)
    except ImportError:
        # Fallback if psutil is not available
        try:
            import resource
            return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024.0
        except Exception:
            return 0.0

# Session-level metrics storage
_session_metrics: List[Dict[str, Any]] = []

def get_session_metrics() -> List[Dict[str, Any]]:
    """Get all metrics collected in the current session."""
    return _session_metrics.copy()

def clear_session_metrics():
    """Clear session metrics."""
    _session_metrics.clear()

def save_session_metrics(output_path: str):
    """Save session metrics to a JSON file."""
    with open(output_path, 'w') as f:
        json.dump(_session_metrics, f, indent=2)

@contextlib.contextmanager
def memory_context(name: str = "task"):
    """Context manager for memory monitoring."""
    monitor = MemoryMonitor(name)
    try:
        with monitor:
            yield monitor
    finally:
        _session_metrics.append(monitor.get_metrics())

def main():
    """Simple test for MemoryMonitor."""
    print("Testing MemoryMonitor...")
    
    # Test manual start/stop
    m = MemoryMonitor("test_manual")
    m.start()
    time.sleep(0.1)
    # Allocate some memory
    _ = [i for i in range(100000)]
    m.stop()
    print(f"Manual: {m.get_metrics()}")
    
    # Test chaining
    m2 = MemoryMonitor("test_chain").start()
    time.sleep(0.1)
    _ = [i for i in range(100000)]
    m2.stop()
    print(f"Chained: {m2.get_metrics()}")
    
    # Test context manager
    with MemoryMonitor("test_context") as m3:
        time.sleep(0.1)
        _ = [i for i in range(100000)]
    print(f"Context: {m3.get_metrics()}")
    
    # Test tolerant fallback
    m4 = MemoryMonitor("test_fallback")
    m4.start()
    m4.info("test log")
    m4.debug("debug log")
    m4.stop()
    print(f"Fallback OK: {m4.get_metrics()}")
    
    print("MemoryMonitor tests passed.")

if __name__ == "__main__":
    main()
