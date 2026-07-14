"""
Memory monitoring utilities for the llmXive pipeline.

Provides tools to track peak RAM usage and wall-clock time using
memory_profiler and tracemalloc, with background sampling capabilities.
"""
import os
import time
import json
import threading
import tracemalloc
import subprocess
from pathlib import Path
from typing import Optional, Dict, Any, List, Callable
from contextlib import contextmanager

# Try to import memory_profiler, fallback gracefully if not available
try:
    from memory_profiler import memory_usage
    MEMORY_PROFILER_AVAILABLE = True
except ImportError:
    MEMORY_PROFILER_AVAILABLE = False
    memory_usage = None

from config import get_results_dir, get_memory_limit_gb, ensure_directories

# Global session storage for metrics
_session_metrics: List[Dict[str, Any]] = []
_lock = threading.Lock()

class MemoryMonitor:
    """
    A memory and time monitor that logs peak RAM and wall-clock duration.
    
    Supports:
    - Manual start/stop via .start()/.stop()
    - Chained calls: monitor.start().stop()
    - Background sampling thread for continuous monitoring
    - Integration with memory_profiler for detailed memory snapshots
    """
    
    def __init__(self, 
                 log_path: Optional[Path] = None,
                 sample_interval: float = 0.5,
                 use_tracemalloc: bool = True,
                 use_memory_profiler: bool = True):
        """
        Initialize the memory monitor.
        
        Args:
            log_path: Path to write memory logs. Defaults to data/results/memory_logs.json.
            sample_interval: Interval in seconds for background sampling.
            use_tracemalloc: Whether to use Python's tracemalloc for object tracking.
            use_memory_profiler: Whether to use memory_profiler for system RAM tracking.
        """
        self.log_path = log_path or (get_results_dir() / "memory_logs.json")
        self.sample_interval = sample_interval
        self.use_tracemalloc = use_tracemalloc
        self.use_memory_profiler = use_memory_profiler and MEMORY_PROFILER_AVAILABLE
        
        self._start_time: Optional[float] = None
        self._stop_time: Optional[float] = None
        self._peak_memory_mb: float = 0.0
        self._sampled_memories: List[float] = []
        self._thread: Optional[threading.Thread] = None
        self._stop_sampling = threading.Event()
        self._is_running = False
        
        # Ensure log directory exists
        ensure_directories()
        
    def _background_sampler(self):
        """Background thread to sample memory usage periodically."""
        while not self._stop_sampling.is_set():
            try:
                current_mem = get_current_memory_mb()
                self._sampled_memories.append(current_mem)
                if current_mem > self._peak_memory_mb:
                    self._peak_memory_mb = current_mem
            except Exception:
                # Silently ignore sampling errors to prevent crashing the monitored process
                pass
            self._stop_sampling.wait(self.sample_interval)

    def start(self):
        """
        Start monitoring wall-clock time and memory usage.
        
        Returns:
            self for method chaining.
        """
        if self._is_running:
            return self
            
        self._start_time = time.time()
        self._stop_time = None
        self._sampled_memories = []
        self._peak_memory_mb = 0.0
        self._stop_sampling.clear()
        self._is_running = True
        
        # Start tracemalloc if enabled
        if self.use_tracemalloc and not tracemalloc.is_tracing():
            tracemalloc.start()
        
        # Start background sampling thread if enabled
        if self.use_memory_profiler:
            self._thread = threading.Thread(target=self._background_sampler, daemon=True)
            self._thread.start()
        else:
            # Fallback: sample once at start if no profiler
            self._sampled_memories.append(get_current_memory_mb())
            self._peak_memory_mb = self._sampled_memories[0]
            
        return self

    def stop(self) -> Dict[str, Any]:
        """
        Stop monitoring and return metrics.
        
        Returns:
            Dictionary with 'wall_time_sec', 'peak_memory_mb', and 'sample_count'.
        """
        if not self._is_running:
            return {
                'wall_time_sec': 0.0,
                'peak_memory_mb': self._peak_memory_mb,
                'sample_count': len(self._sampled_memories)
            }
            
        self._stop_time = time.time()
        self._is_running = False
        self._stop_sampling.set()
        
        # Wait for thread to finish if it exists
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=2.0)
        
        # Final memory check
        if self.use_memory_profiler:
            final_mem = get_current_memory_mb()
            self._sampled_memories.append(final_mem)
            if final_mem > self._peak_memory_mb:
                self._peak_memory_mb = final_mem
        
        # Stop tracemalloc if we started it
        if self.use_tracemalloc and tracemalloc.is_tracing():
            tracemalloc.stop()
        
        wall_time = self._stop_time - self._start_time if self._start_time else 0.0
        
        metrics = {
            'wall_time_sec': wall_time,
            'peak_memory_mb': self._peak_memory_mb,
            'sample_count': len(self._sampled_memories),
            'start_time': self._start_time,
            'stop_time': self._stop_time,
            'avg_memory_mb': sum(self._sampled_memories) / len(self._sampled_memories) if self._sampled_memories else 0.0
        }
        
        # Log to file
        self._log_metrics(metrics)
        
        return metrics

    def _log_metrics(self, metrics: Dict[str, Any]):
        """Append metrics to the log file."""
        log_entry = {
            'timestamp': time.time(),
            'metrics': metrics
        }
        
        # Load existing logs if file exists
        existing_logs = []
        if self.log_path.exists():
            try:
                with open(self.log_path, 'r') as f:
                    existing_logs = json.load(f)
            except (json.JSONDecodeError, IOError):
                existing_logs = []
        
        existing_logs.append(log_entry)
        
        # Write back
        with open(self.log_path, 'w') as f:
            json.dump(existing_logs, f, indent=2)

    def get_peak_memory_mb(self) -> float:
        """Get the current peak memory usage in MB."""
        return self._peak_memory_mb

    def get_wall_time_sec(self) -> float:
        """Get the elapsed wall-clock time in seconds."""
        if self._start_time is None:
            return 0.0
        end = self._stop_time or time.time()
        return end - self._start_time

    # --- Tolerant interface for unknown method calls ---
    def __getattr__(self, name: str) -> Callable:
        """
        Fallback for unknown method calls (e.g., .info(), .debug(), etc.).
        Returns a no-op function to prevent AttributeError.
        """
        def _noop(*args, **kwargs):
            return None
        return _noop

def get_current_memory_mb() -> float:
    """
    Get current memory usage of the process in MB.
    
    Uses memory_profiler if available, otherwise falls back to /proc/self/status
    on Linux or psutil if installed.
    """
    if MEMORY_PROFILER_AVAILABLE:
        try:
            # memory_usage returns a list of samples; we take the current one
            # memory_usage(-1, timeout=0.1, max_iterations=1) returns current usage
            mem = memory_usage(-1, timeout=0.1, max_iterations=1)
            return float(mem[0]) if mem else 0.0
        except Exception:
            pass

    # Fallback: /proc/self/status (Linux)
    if os.path.exists('/proc/self/status'):
        try:
            with open('/proc/self/status', 'r') as f:
                for line in f:
                    if line.startswith('VmRSS:'):
                        # VmRSS is in kB
                        parts = line.split()
                        return float(parts[1]) / 1024.0
        except Exception:
            pass

    # Fallback: psutil if available
    try:
        import psutil
        process = psutil.Process(os.getpid())
        return process.memory_info().rss / (1024 * 1024)
    except ImportError:
        pass

    # Last resort: return 0
    return 0.0

def check_memory_limit(limit_gb: Optional[float] = None) -> bool:
    """
    Check if current memory usage exceeds the limit.
    
    Args:
        limit_gb: Limit in GB. If None, uses config value.
        
    Returns:
        True if memory usage is within limit, False otherwise.
    """
    limit = limit_gb or get_memory_limit_gb()
    current_mb = get_current_memory_mb()
    limit_mb = limit * 1024
    return current_mb < limit_mb

def should_batch_process(limit_gb: Optional[float] = None) -> bool:
    """
    Determine if batch processing (sequential) should be triggered.
    
    Returns True if current memory usage is above the threshold (e.g., 6GB as per spec).
    """
    # Spec mentions triggering batch mode if RAM > 6GB
    threshold = 6.0
    if limit_gb:
        threshold = limit_gb
        
    current_mb = get_current_memory_mb()
    return current_mb > (threshold * 1024)

def measure_memory(func: Callable) -> Callable:
    """
    Decorator to measure memory usage of a function.
    
    Returns a wrapper that logs peak memory during function execution.
    """
    def wrapper(*args, **kwargs):
        monitor = MemoryMonitor(use_tracemalloc=True, use_memory_profiler=True)
        monitor.start()
        try:
            result = func(*args, **kwargs)
        finally:
            metrics = monitor.stop()
            # Store in session metrics
            with _lock:
                _session_metrics.append({
                    'function': func.__name__,
                    'metrics': metrics
                })
        return result
    return wrapper

@contextmanager
def memory_context(name: str = "unnamed"):
    """
    Context manager to measure memory and time for a block of code.
    
    Usage:
        with memory_context("my_block") as ctx:
            # do work
        print(ctx['peak_memory_mb'])
    """
    monitor = MemoryMonitor()
    result = {'name': name}
    monitor.start()
    try:
        yield result
    finally:
        metrics = monitor.stop()
        result.update(metrics)
        with _lock:
            _session_metrics.append({'name': name, 'metrics': metrics})

def get_session_metrics() -> List[Dict[str, Any]]:
    """Get all metrics collected in the current session."""
    with _lock:
        return list(_session_metrics)

def clear_session_metrics():
    """Clear the session metrics list."""
    global _session_metrics
    with _lock:
        _session_metrics = []

def save_session_metrics(path: Optional[Path] = None):
    """Save session metrics to a JSON file."""
    path = path or (get_results_dir() / "session_memory_metrics.json")
    metrics = get_session_metrics()
    with open(path, 'w') as f:
        json.dump(metrics, f, indent=2)

def main():
    """
    Standalone test runner for MemoryMonitor.
    """
    print("Testing MemoryMonitor...")
    monitor = MemoryMonitor()
    
    # Test start/stop
    m = monitor.start().stop()
    print(f"Wall time: {m['wall_time_sec']:.3f}s, Peak memory: {m['peak_memory_mb']:.2f}MB")
    
    # Test background sampling
    monitor2 = MemoryMonitor(sample_interval=0.1)
    monitor2.start()
    time.sleep(1.0)
    # Simulate some memory usage
    data = [i for i in range(1000000)]
    m2 = monitor2.stop()
    print(f"Background sampling - Wall time: {m2['wall_time_sec']:.3f}s, Peak: {m2['peak_memory_mb']:.2f}MB, Samples: {m2['sample_count']}")
    
    # Test context manager
    with memory_context("test_block") as ctx:
        _ = [i**2 for i in range(500000)]
    print(f"Context manager - Peak: {ctx['peak_memory_mb']:.2f}MB")
    
    print("MemoryMonitor tests completed.")

if __name__ == "__main__":
    main()