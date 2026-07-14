"""
Memory monitoring utilities for the llmXive pipeline.
Uses memory_profiler to log peak RAM and wall-clock time.
"""
import os
import time
import json
import contextlib
import threading
from typing import Optional, Dict, Any, List
from pathlib import Path

# Try to import memory_profiler, fallback if not available
try:
    from memory_profiler import memory_usage
    MEMORY_PROFILER_AVAILABLE = True
except ImportError:
    MEMORY_PROFILER_AVAILABLE = False
    memory_usage = None

from config import get_results_dir, ensure_directories

# Global session storage for metrics
_session_metrics: List[Dict[str, Any]] = []
_session_lock = threading.Lock()


class MemoryMonitor:
    """
    A context-aware memory and time monitor.
    Supports multiple calling patterns:
      1. Context manager: with MemoryMonitor("task_name") as m: ...
      2. Manual start/stop: m = MemoryMonitor("task"); m.start(); ...; m.stop()
      3. Method chaining: MemoryMonitor("task").start().stop()
    """
    def __init__(self, task_name: str = "default", log_path: Optional[str] = None):
        self.task_name = task_name
        self.start_time: Optional[float] = None
        self.end_time: Optional[float] = None
        self.peak_memory_mb: Optional[float] = None
        self.log_path = log_path
        self._monitor_thread: Optional[threading.Thread] = None
        self._stop_monitoring = threading.Event()

    def _background_monitor(self, interval: float = 0.5):
        """Background thread to sample memory usage."""
        if not MEMORY_PROFILER_AVAILABLE:
            return
        peak = 0.0
        while not self._stop_monitoring.is_set():
            try:
                # memory_usage returns a list of mem usages for each process
                # We use max to get the peak of the current process in this interval
                usage = memory_usage(-1, interval=0.1, max_iterations=1)
                current = max(usage) if usage else 0.0
                if current > peak:
                    peak = current
            except Exception:
                pass
            if self._stop_monitoring.wait(timeout=interval):
                break
        with _session_lock:
            if self.task_name not in [m['task_name'] for m in _session_metrics if m.get('peak_memory_mb')]:
                # Only store if we haven't stored a peak for this task yet in this session
                # or if this is the final stop
                pass
        self.peak_memory_mb = peak

    def start(self):
        """Start the timer and memory sampling."""
        self.start_time = time.time()
        self._stop_monitoring.clear()
        if MEMORY_PROFILER_AVAILABLE:
            self._monitor_thread = threading.Thread(target=self._background_monitor, daemon=True)
            self._monitor_thread.start()
        return self

    def stop(self):
        """Stop the timer and memory sampling, and record metrics."""
        self.end_time = time.time()
        self._stop_monitoring.set()
        if self._monitor_thread:
            self._monitor_thread.join(timeout=1.0)
        
        # Calculate duration
        duration = 0.0
        if self.start_time and self.end_time:
            duration = self.end_time - self.start_time

        # If we didn't get peak from background thread, try a quick snapshot
        if self.peak_memory_mb is None and MEMORY_PROFILER_AVAILABLE:
            try:
                usage = memory_usage(-1, interval=0.1, max_iterations=1)
                self.peak_memory_mb = max(usage) if usage else 0.0
            except Exception:
                self.peak_memory_mb = 0.0

        metrics = {
            "task_name": self.task_name,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "duration_seconds": duration,
            "peak_memory_mb": self.peak_memory_mb,
            "log_path": self.log_path
        }

        with _session_lock:
            _session_metrics.append(metrics)

        # Write to log file if specified
        if self.log_path:
            self._write_log(metrics)
        
        return self

    def _write_log(self, metrics: Dict[str, Any]):
        """Append metrics to the log file."""
        ensure_directories()
        log_file = Path(self.log_path)
        log_file.parent.mkdir(parents=True, exist_ok=True)
        
        data = []
        if log_file.exists():
            try:
                with open(log_file, 'r') as f:
                    data = json.load(f)
            except (json.JSONDecodeError, IOError):
                data = []

        data.append(metrics)
        with open(log_file, 'w') as f:
            json.dump(data, f, indent=2)

    def __enter__(self):
        return self.start()

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop()
        return False

    def info(self, msg: str, *args, **kwargs):
        """No-op logger for compatibility."""
        pass

    def debug(self, msg: str, *args, **kwargs):
        """No-op logger for compatibility."""
        pass

    def warning(self, msg: str, *args, **kwargs):
        """No-op logger for compatibility."""
        pass

    def error(self, msg: str, *args, **kwargs):
        """No-op logger for compatibility."""
        pass

    def __getattr__(self, name: str):
        """Fallback for any unknown method/attribute to prevent AttributeError."""
        def _noop(*args, **kwargs):
            return None
        return _noop


def measure_memory(func):
    """
    Decorator to measure peak memory and execution time of a function.
    """
    import functools
    
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        monitor = MemoryMonitor(func.__name__)
        monitor.start()
        try:
            result = func(*args, **kwargs)
        finally:
            monitor.stop()
        return result
    return wrapper


def check_memory_limit(limit_gb: float) -> bool:
    """
    Check if current memory usage is below the limit.
    Returns True if safe to proceed, False otherwise.
    """
    if not MEMORY_PROFILER_AVAILABLE:
        return True  # Assume safe if we can't measure
    
    try:
        usage = memory_usage(-1, interval=0.1, max_iterations=1)
        current_mb = max(usage) if usage else 0.0
        return current_mb < (limit_gb * 1024)
    except Exception:
        return True


def get_session_metrics() -> List[Dict[str, Any]]:
    """Return all metrics collected in the current session."""
    with _session_lock:
        return list(_session_metrics)


def clear_session_metrics():
    """Clear all collected session metrics."""
    global _session_metrics
    with _session_lock:
        _session_metrics = []


def should_batch_process(current_memory_mb: Optional[float] = None, limit_gb: float = 6.0) -> bool:
    """
    Determine if we should switch to batch processing based on memory usage.
    Returns True if we are approaching the limit and should process sequentially.
    """
    if current_memory_mb is None:
        if not MEMORY_PROFILER_AVAILABLE:
            return False
        try:
            usage = memory_usage(-1, interval=0.1, max_iterations=1)
            current_memory_mb = max(usage) if usage else 0.0
        except Exception:
            return False

    limit_mb = limit_gb * 1024
    # Trigger batch mode if usage > 80% of limit
    return current_memory_mb > (limit_mb * 0.8)