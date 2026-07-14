"""
Memory management utilities for CPU-tractable agent execution.

Implements:
- Memory monitoring and adaptive throttling
- Garbage collection tuning for large object graphs
- Batch processing with memory constraints
- Cache eviction policies for context retrieval
"""
import gc
import os
import sys
import resource
import traceback
from typing import Any, Dict, List, Optional, Callable, TypeVar, ContextManager
from contextlib import contextmanager
import weakref
import threading
from pathlib import Path

# Configuration constants (can be overridden via environment variables)
DEFAULT_MEMORY_LIMIT_MB = int(os.environ.get("LLMXIVE_MEMORY_LIMIT_MB", "6500"))
DEFAULT_GC_THRESHOLD = int(os.environ.get("LLMXIVE_GC_THRESHOLD", "700"))
DEFAULT_CACHE_SIZE = int(os.environ.get("LLMXIVE_CACHE_SIZE", "100"))
MEMORY_CHECK_INTERVAL = int(os.environ.get("LLMXIVE_MEMORY_CHECK_INTERVAL", "5"))  # seconds

T = TypeVar('T')

class MemoryExhaustedError(Exception):
    """Raised when memory usage exceeds the configured limit."""
    pass

class MemoryMonitor:
    """
    Monitors memory usage and provides throttling mechanisms.
    Uses resource module for cross-platform compatibility (Linux/macOS).
    """
    
    def __init__(self, limit_mb: int = DEFAULT_MEMORY_LIMIT_MB):
        self.limit_mb = limit_mb
        self.limit_bytes = limit_mb * 1024 * 1024
        self._lock = threading.Lock()
        self._callbacks: List[Callable[[], None]] = []
        self._is_monitoring = False
        self._monitor_thread: Optional[threading.Thread] = None
    
    def get_current_usage_mb(self) -> float:
        """Get current memory usage in MB."""
        try:
            usage = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
            # On macOS, ru_maxrss is in bytes; on Linux, it's in KB
            if sys.platform == 'darwin':
                return usage / (1024 * 1024)
            else:
                return usage / 1024
        except Exception:
            # Fallback to os module if resource fails
            try:
                # This is a rough estimate
                return float(os.popen('ps -o rss= -p $PPID').read().strip()) / 1024
            except Exception:
                return 0.0
    
    def check_and_throttle(self) -> bool:
        """
        Check memory usage and perform emergency cleanup if needed.
        Returns True if cleanup was performed, False otherwise.
        """
        current_mb = self.get_current_usage_mb()
        
        if current_mb > self.limit_mb * 0.9:
            # Critical: Immediate cleanup
            self._emergency_cleanup()
            return True
        elif current_mb > self.limit_mb * 0.7:
            # Warning: Normal cleanup
            self._normal_cleanup()
            return True
        
        return False
    
    def _normal_cleanup(self):
        """Perform standard garbage collection and cache clearing."""
        gc.collect()
        # Clear any registered caches
        for callback in self._callbacks:
            try:
                callback()
            except Exception:
                pass
    
    def _emergency_cleanup(self):
        """Aggressive cleanup for critical memory situations."""
        # Force multiple GC passes
        for _ in range(3):
            gc.collect()
            if self.get_current_usage_mb() < self.limit_mb * 0.8:
                break
        
        # Clear all registered callbacks
        for callback in self._callbacks:
            try:
                callback()
            except Exception:
                pass
        
        # Log warning
        current_mb = self.get_current_usage_mb()
        if current_mb > self.limit_mb * 0.95:
            raise MemoryExhaustedError(
                f"Memory usage critical: {current_mb:.1f}MB / {self.limit_mb}MB limit. "
                "Consider reducing batch size or sample size."
            )
    
    def register_cache_clear(self, callback: Callable[[], None]):
        """Register a callback to clear a specific cache."""
        with self._lock:
            self._callbacks.append(callback)
    
    def start_monitoring(self, interval: int = MEMORY_CHECK_INTERVAL):
        """Start background monitoring thread."""
        if self._is_monitoring:
            return
        
        self._is_monitoring = True
        
        def monitor_loop():
            while self._is_monitoring:
                try:
                    self.check_and_throttle()
                except MemoryExhaustedError:
                    raise
                except Exception:
                    pass  # Ignore errors in monitoring
                import time
                time.sleep(interval)
        
        self._monitor_thread = threading.Thread(target=monitor_loop, daemon=True)
        self._monitor_thread.start()
    
    def stop_monitoring(self):
        """Stop background monitoring."""
        self._is_monitoring = False
        if self._monitor_thread:
            self._monitor_thread.join(timeout=2.0)
            self._monitor_thread = None

@contextmanager
def memory_limited(limit_mb: Optional[int] = None) -> MemoryMonitor:
    """
    Context manager that enforces memory limits within a block.
    
    Usage:
    with memory_limited(5000) as monitor:
        # Your code here
        monitor.check_and_throttle()
    """
    limit = limit_mb or DEFAULT_MEMORY_LIMIT_MB
    monitor = MemoryMonitor(limit)
    
    # Set GC threshold to be more aggressive
    original_threshold = gc.get_threshold()
    gc.set_threshold(DEFAULT_GC_THRESHOLD)
    
    try:
        yield monitor
    finally:
        gc.set_threshold(original_threshold)
        monitor.check_and_throttle()
        gc.collect()

class LRUContextCache:
    """
    Thread-safe LRU cache for retrieved context to prevent memory bloat.
    Automatically evicts least recently used items when limit is reached.
    """
    
    def __init__(self, max_size: int = DEFAULT_CACHE_SIZE):
        self.max_size = max_size
        self._cache: Dict[str, Any] = {}
        self._access_order: List[str] = []
        self._lock = threading.Lock()
    
    def get(self, key: str) -> Optional[Any]:
        """Get item from cache and update access order."""
        with self._lock:
            if key not in self._cache:
                return None
            
            # Move to end (most recently used)
            self._access_order.remove(key)
            self._access_order.append(key)
            return self._cache[key]
    
    def put(self, key: str, value: Any):
        """Add item to cache, evicting LRU if necessary."""
        with self._lock:
            if key in self._cache:
                self._access_order.remove(key)
            
            self._cache[key] = value
            self._access_order.append(key)
            
            # Evict if over limit
            while len(self._cache) > self.max_size:
                oldest_key = self._access_order.pop(0)
                del self._cache[oldest_key]
    
    def clear(self):
        """Clear entire cache."""
        with self._lock:
            self._cache.clear()
            self._access_order.clear()
    
    def __len__(self) -> int:
        return len(self._cache)

def optimize_gc_for_large_graphs():
    """
    Tune garbage collector for better performance with large object graphs.
    Call this before processing large datasets.
    """
    # Increase threshold to reduce GC frequency during processing
    # but ensure it doesn't get too high
    current = gc.get_threshold()
    if current[2] < DEFAULT_GC_THRESHOLD:
        gc.set_threshold(
            max(current[0], 700),
            max(current[1], 10),
            DEFAULT_GC_THRESHOLD
        )
    
    # Enable debug stats for troubleshooting (can be disabled in production)
    # gc.set_debug(gc.DEBUG_STATS)

def get_memory_profile() -> Dict[str, Any]:
    """
    Get a detailed memory profile of the current process.
    Useful for debugging memory issues.
    """
    usage = resource.getrusage(resource.RUSAGE_SELF)
    
    profile = {
        "max_rss_mb": usage.ru_maxrss / 1024 if sys.platform != 'darwin' else usage.ru_maxrss / (1024 * 1024),
        "shared_mem_kb": usage.ru_ixrss,
        "unshared_data_kb": usage.ru_idrss,
        "unshared_stack_kb": usage.ru_isrss,
        "page_faults": usage.ru_majflt,
        "voluntary_context_switches": usage.ru_nvcsw,
        "involuntary_context_switches": usage.ru_nivcsw,
    }
    
    return profile

def batch_process_with_memory_control(
    items: List[T],
    processor: Callable[[T], Any],
    batch_size: int = 10,
    memory_monitor: Optional[MemoryMonitor] = None
) -> List[Any]:
    """
    Process items in batches with automatic memory management.
    
    Args:
        items: List of items to process
        processor: Function to apply to each item
        batch_size: Number of items to process before checking memory
        memory_monitor: Optional memory monitor instance
    
    Returns:
        List of results
    """
    results = []
    monitor = memory_monitor or MemoryMonitor()
    
    for i in range(0, len(items), batch_size):
        batch = items[i:i + batch_size]
        
        # Process batch
        batch_results = []
        for item in batch:
            try:
                result = processor(item)
                batch_results.append(result)
            except Exception as e:
                # Log but continue with other items
                print(f"Error processing item: {e}", file=sys.stderr)
                batch_results.append(None)
        
        results.extend(batch_results)
        
        # Check memory after each batch
        if i + batch_size < len(items):
            if monitor.check_and_throttle():
                # Force a small sleep to allow OS to reclaim memory
                import time
                time.sleep(0.1)
    
    return results

def clean_up_large_objects(objs: List[Any]):
    """
    Explicitly clean up large objects by breaking references.
    Useful for clearing large data structures after processing.
    """
    for obj in objs:
        try:
            # Try to clear common attributes
            if hasattr(obj, '__dict__'):
                obj.__dict__.clear()
            if hasattr(obj, '__slots__'):
                for slot in obj.__slots__:
                    if hasattr(obj, slot):
                        setattr(obj, slot, None)
        except Exception:
            pass
    
    # Force garbage collection
    gc.collect()

# Global monitor instance for the process
_global_monitor: Optional[MemoryMonitor] = None
_monitor_lock = threading.Lock()

def get_global_monitor() -> MemoryMonitor:
    """Get or create the global memory monitor."""
    global _global_monitor
    with _monitor_lock:
        if _global_monitor is None:
            _global_monitor = MemoryMonitor()
        return _global_monitor

def main():
    """Command-line interface for memory management utilities."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Memory management utilities for llmXive")
    parser.add_argument("--limit", type=int, default=DEFAULT_MEMORY_LIMIT_MB,
                      help=f"Memory limit in MB (default: {DEFAULT_MEMORY_LIMIT_MB})")
    parser.add_argument("--profile", action="store_true",
                      help="Print memory profile and exit")
    parser.add_argument("--test", action="store_true",
                      help="Run memory test simulation")
    
    args = parser.parse_args()
    
    if args.profile:
        profile = get_memory_profile()
        print("Memory Profile:")
        for key, value in profile.items():
            print(f"  {key}: {value}")
        return
    
    if args.test:
        print(f"Starting memory test with limit: {args.limit}MB")
        monitor = MemoryMonitor(args.limit)
        
        # Simulate some processing
        test_data = []
        for i in range(1000):
            test_data.append([j for j in range(1000)])
            if i % 100 == 0:
                used = monitor.get_current_usage_mb()
                print(f"  Iteration {i}: {used:.1f}MB used")
                monitor.check_and_throttle()
        
        print(f"Final memory: {monitor.get_current_usage_mb():.1f}MB")
        print("Test completed successfully")
        return
    
    print(f"Memory limit set to {args.limit}MB")
    print("Use memory_limited() context manager or get_global_monitor() in your code")

if __name__ == "__main__":
    main()
