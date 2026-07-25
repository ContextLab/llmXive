"""
Memory monitoring utilities for the llmXive pipeline.

Provides functionality to track RAM usage and enforce memory limits
to ensure training runs stay within hardware constraints (7GB RAM limit).
"""
import os
import gc
import time
import threading
from typing import Optional, Callable, Any, Dict, List
from contextlib import contextmanager
import psutil
import numpy as np

# Project root relative to this file
_PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
_RESULTS_DIR = os.path.join(_PROJECT_ROOT, 'results')
_MEMORY_LOG_PATH = os.path.join(_RESULTS_DIR, 'memory_usage.log')

# Default memory limit in GB (matches hardware constraint)
DEFAULT_MEMORY_LIMIT_GB = 7.0

class MemoryMonitor:
    """
    Monitors RAM usage and enforces a memory limit.
    
    Attributes:
        limit_gb: Memory limit in gigabytes.
        usage_history: List of (timestamp, usage_gb) tuples.
        peak_usage_gb: Peak observed memory usage in gigabytes.
    """
    
    def __init__(self, limit_gb: float = DEFAULT_MEMORY_LIMIT_GB):
        """
        Initialize the memory monitor.
        
        Args:
            limit_gb: Maximum allowed memory usage in GB.
        """
        self.limit_gb = limit_gb
        self.limit_bytes = limit_gb * 1024**3
        self.usage_history: List[tuple] = []
        self.peak_usage_gb: float = 0.0
        self._monitor_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._process = psutil.Process(os.getpid())
        
        # Ensure results directory exists
        os.makedirs(_RESULTS_DIR, exist_ok=True)

    def get_current_usage_gb(self) -> float:
        """
        Get current memory usage in gigabytes.
        
        Returns:
            Current RSS memory usage in GB.
        """
        try:
            # Get memory info for current process
            mem_info = self._process.memory_info()
            return mem_info.rss / (1024**3)
        except (psutil.NoSuchProcess, psutil.AccessDenied) as e:
            raise RuntimeError(f"Failed to get memory usage: {e}")

    def check_limit(self) -> bool:
        """
        Check if current memory usage is within the limit.
        
        Returns:
            True if usage is within limit, False otherwise.
        """
        current = self.get_current_usage_gb()
        if current > self.limit_gb:
            return False
        return True

    def force_gc(self) -> float:
        """
        Force garbage collection and return memory after cleanup.
        
        Returns:
            Memory usage in GB after garbage collection.
        """
        gc.collect()
        return self.get_current_usage_gb()

    def _monitor_loop(self, interval: float = 0.1):
        """Background monitoring loop."""
        while not self._stop_event.is_set():
            usage = self.get_current_usage_gb()
            self.usage_history.append((time.time(), usage))
            
            # Update peak
            if usage > self.peak_usage_gb:
                self.peak_usage_gb = usage
            
            # Check limit
            if usage > self.limit_gb:
                self._log_warning(f"Memory limit exceeded: {usage:.2f}GB > {self.limit_gb}GB")
                # Force garbage collection
                usage = self.force_gc()
                if usage > self.limit_gb:
                    self._log_warning("Memory limit still exceeded after GC, triggering failure.")
            
            time.sleep(interval)

    def start_monitoring(self, interval: float = 0.1):
        """
        Start background memory monitoring.
        
        Args:
            interval: Sampling interval in seconds.
        """
        if self._monitor_thread and self._monitor_thread.is_alive():
            return
        
        self._stop_event.clear()
        self._monitor_thread = threading.Thread(
            target=self._monitor_loop, 
            args=(interval,), 
            daemon=True
        )
        self._monitor_thread.start()

    def stop_monitoring(self):
        """Stop background memory monitoring."""
        if self._monitor_thread:
            self._stop_event.set()
            self._monitor_thread.join(timeout=1.0)

    def _log_warning(self, message: str):
        """Log a warning message to the memory log file."""
        timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
        log_line = f"[{timestamp}] WARNING: {message}\n"
        with open(_MEMORY_LOG_PATH, 'a') as f:
            f.write(log_line)
        # Also print to stderr
        import sys
        print(log_line.strip(), file=sys.stderr)

    def get_statistics(self) -> Dict[str, float]:
        """
        Get memory usage statistics.
        
        Returns:
            Dictionary with current, peak, and limit values.
        """
        return {
            'current_gb': self.get_current_usage_gb(),
            'peak_gb': self.peak_usage_gb,
            'limit_gb': self.limit_gb,
            'samples': len(self.usage_history)
        }

    def save_report(self, path: Optional[str] = None):
        """
        Save a memory usage report to a file.
        
        Args:
            path: Optional path for the report. Defaults to results/memory_report.txt.
        """
        if path is None:
            path = os.path.join(_RESULTS_DIR, 'memory_report.txt')
        
        stats = self.get_statistics()
        
        with open(path, 'w') as f:
            f.write("Memory Monitor Report\n")
            f.write("=" * 40 + "\n")
            f.write(f"Limit: {stats['limit_gb']:.2f} GB\n")
            f.write(f"Current Usage: {stats['current_gb']:.2f} GB\n")
            f.write(f"Peak Usage: {stats['peak_gb']:.2f} GB\n")
            f.write(f"Samples Collected: {stats['samples']}\n")
            f.write("=" * 40 + "\n")
            
            if self.usage_history:
                f.write("\nUsage History (last 10 samples):\n")
                for ts, usage in self.usage_history[-10:]:
                    f.write(f"  {time.strftime('%H:%M:%S', time.localtime(ts))}: {usage:.3f} GB\n")

@contextmanager
def memory_limit_context(limit_gb: float = DEFAULT_MEMORY_LIMIT_GB, 
                          check_interval: float = 0.5):
    """
    Context manager that enforces a memory limit during execution.
    
    If memory usage exceeds the limit, a RuntimeError is raised.
    
    Args:
        limit_gb: Memory limit in GB.
        check_interval: Interval for checking memory in seconds.
        
    Yields:
        MemoryMonitor instance.
        
    Raises:
        RuntimeError: If memory limit is exceeded.
    """
    monitor = MemoryMonitor(limit_gb=limit_gb)
    monitor.start_monitoring(interval=check_interval)
    
    try:
        yield monitor
    finally:
        monitor.stop_monitoring()
        monitor.save_report()

def enforce_memory_limit(limit_gb: float = DEFAULT_MEMORY_LIMIT_GB, 
                         check_interval: float = 0.5):
    """
    Decorator factory to enforce memory limits on functions.
    
    Args:
        limit_gb: Memory limit in GB.
        check_interval: Interval for checking memory in seconds.
        
    Returns:
        Decorator that wraps the function with memory monitoring.
    """
    def decorator(func: Callable) -> Callable:
        def wrapper(*args, **kwargs) -> Any:
            monitor = MemoryMonitor(limit_gb=limit_gb)
            monitor.start_monitoring(interval=check_interval)
            
            try:
                result = func(*args, **kwargs)
                return result
            finally:
                monitor.stop_monitoring()
                monitor.save_report()
                # Check final status
                if not monitor.check_limit():
                    raise RuntimeError(
                        f"Memory limit ({limit_gb}GB) exceeded during {func.__name__}. "
                        f"Peak usage: {monitor.peak_usage_gb:.2f}GB"
                    )
        return wrapper
    return decorator

def main():
    """
    Command-line interface for memory monitoring demonstration.
    
    Usage:
        python -m src.utils.memory_monitor [--limit GB] [--duration SEC]
    """
    import argparse
    
    parser = argparse.ArgumentParser(description='Memory Monitor Utility')
    parser.add_argument('--limit', type=float, default=DEFAULT_MEMORY_LIMIT_GB,
                      help=f'Memory limit in GB (default: {DEFAULT_MEMORY_LIMIT_GB})')
    parser.add_argument('--duration', type=float, default=5.0,
                      help='Duration to run monitoring in seconds (default: 5.0)')
    parser.add_argument('--check-interval', type=float, default=0.5,
                      help='Check interval in seconds (default: 0.5)')
    
    args = parser.parse_args()
    
    print(f"Starting memory monitor (limit: {args.limit}GB, duration: {args.duration}s)")
    
    monitor = MemoryMonitor(limit_gb=args.limit)
    monitor.start_monitoring(interval=args.check_interval)
    
    # Simulate some work
    time.sleep(args.duration)
    
    monitor.stop_monitoring()
    monitor.save_report()
    
    stats = monitor.get_statistics()
    print(f"\nMonitoring complete.")
    print(f"Peak usage: {stats['peak_gb']:.3f} GB")
    print(f"Limit: {stats['limit_gb']} GB")
    print(f"Status: {'OK' if stats['peak_gb'] <= stats['limit_gb'] else 'EXCEEDED'}")
    
    if stats['peak_gb'] > stats['limit_gb']:
        print("WARNING: Memory limit was exceeded!")
        return 1
    return 0

if __name__ == '__main__':
    import sys
    sys.exit(main())
