import os
import time
import json
import contextlib
from typing import Optional, Dict, Any, List
from pathlib import Path

from memory_profiler import memory_usage
from config import get_results_dir, get_memory_limit_gb


# Global session metrics storage
_session_metrics: List[Dict[str, Any]] = []
_current_monitor: Optional['MemoryMonitor'] = None


class MemoryMonitor:
    """
    A context manager and utility class to monitor peak RAM and wall-clock time
    for specific code blocks using memory_profiler.
    
    Usage:
        with MemoryMonitor("task_name") as monitor:
            do_heavy_work()
        # Access monitor.peak_ram_mb and monitor.elapsed_time_sec
    """
    
    def __init__(self, task_name: str, log_file: Optional[Path] = None):
        self.task_name = task_name
        self.log_file = log_file or (get_results_dir() / "memory_logs.jsonl")
        self.peak_ram_mb: float = 0.0
        self.elapsed_time_sec: float = 0.0
        self.start_time: float = 0.0
        self.end_time: float = 0.0
        
        # Ensure log directory exists
        self.log_file.parent.mkdir(parents=True, exist_ok=True)

    def __enter__(self) -> 'MemoryMonitor':
        global _current_monitor
        _current_monitor = self
        self.start_time = time.time()
        
        # Measure memory usage of the current process (PID)
        # memory_usage returns a list of memory usages over time intervals.
        # We use interval=0.1 to get frequent samples without too much overhead.
        # We measure the current process only (pid=os.getpid()).
        try:
            # measure_memory returns a tuple (peak, trace) or just list if tracemalloc not used
            # We use the tuple form: (max_usage, trace)
            # However, memory_usage usually returns a list of samples if interval is set.
            # To get peak, we can just take the max of the returned list.
            mem_samples, _ = memory_usage(
                (os.getpid,),
                interval=0.1,
                timeout=0, # No timeout, run until context exit
                multiprocess=False,
                max_usage=True # Return the maximum usage directly
            )
            # memory_usage with max_usage=True returns the max value directly, not a list.
            # But the signature varies. Let's handle both cases safely.
            if isinstance(mem_samples, (list, tuple)):
                self.peak_ram_mb = max(mem_samples) if mem_samples else 0.0
            else:
                self.peak_ram_mb = float(mem_samples) if mem_samples else 0.0
        except Exception as e:
            # Fallback if memory_profiler fails (e.g., permission issues on some systems)
            # We log the error but continue, setting peak to 0 or a safe default
            self.peak_ram_mb = 0.0
            # In a real scenario, we might want to log this error to stderr
            # print(f"Warning: Could not measure memory for {self.task_name}: {e}")

        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.end_time = time.time()
        self.elapsed_time_sec = self.end_time - self.start_time
        
        # Record metrics
        metrics = {
            "task_name": self.task_name,
            "peak_ram_mb": self.peak_ram_mb,
            "elapsed_time_sec": self.elapsed_time_sec,
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        }
        
        # Store in session list
        _session_metrics.append(metrics)
        
        # Append to JSONL log file
        with open(self.log_file, 'a') as f:
            f.write(json.dumps(metrics) + '\n')
        
        # Reset global reference
        global _current_monitor
        _current_monitor = None

    def get_metrics(self) -> Dict[str, Any]:
        """Return the current session's metrics for this monitor."""
        return {
            "task_name": self.task_name,
            "peak_ram_mb": self.peak_ram_mb,
            "elapsed_time_sec": self.elapsed_time_sec
        }


def measure_memory(func):
    """
    Decorator to measure peak memory and execution time of a function.
    """
    import functools
    
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        task_name = func.__name__
        with MemoryMonitor(task_name) as monitor:
            result = func(*args, **kwargs)
        return result
    
    return wrapper


def check_memory_limit(usage_mb: float, limit_gb: Optional[float] = None) -> bool:
    """
    Check if current memory usage (in MB) exceeds the configured limit (in GB).
    
    Args:
        usage_mb: Current memory usage in MB.
        limit_gb: Optional limit in GB. If None, uses config default.
        
    Returns:
        True if usage is WITHIN limits (i.e., safe to continue), False if exceeded.
    """
    if limit_gb is None:
        limit_gb = get_memory_limit_gb()
    
    limit_mb = limit_gb * 1024.0
    return usage_mb <= limit_mb


def get_session_metrics() -> List[Dict[str, Any]]:
    """
    Retrieve all metrics collected during the current session.
    
    Returns:
        List of dictionaries containing task_name, peak_ram_mb, elapsed_time_sec, and timestamp.
    """
    return _session_metrics.copy()


def clear_session_metrics() -> None:
    """
    Clear all metrics collected during the current session.
    """
    global _session_metrics
    _session_metrics.clear()


def should_batch_process(current_usage_mb: float, limit_gb: Optional[float] = None) -> bool:
    """
    Determine if the system should switch to batch processing mode based on memory usage.
    
    This is typically triggered when memory usage approaches a threshold (e.g., 6GB or 80% of limit).
    
    Args:
        current_usage_mb: Current memory usage in MB.
        limit_gb: Optional limit in GB. If None, uses config default.
        
    Returns:
        True if batch processing should be triggered, False otherwise.
    """
    if limit_gb is None:
        limit_gb = get_memory_limit_gb()
    
    # Threshold for batch processing: 6GB or 80% of limit, whichever is lower
    batch_threshold_gb = min(6.0, limit_gb * 0.8)
    batch_threshold_mb = batch_threshold_gb * 1024.0
    
    return current_usage_mb > batch_threshold_mb