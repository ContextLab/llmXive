import os
import time
import json
import contextlib
from typing import Optional, Dict, Any, List
from pathlib import Path
from config import get_results_dir

class MemoryMonitor:
    def __init__(self, limit_gb: float = 8.0):
        self.limit_gb = limit_gb
        self.session_metrics: List[Dict[str, Any]] = []
        self.start_time: Optional[float] = None

    def start_session(self, task_name: str) -> None:
        self.start_time = time.time()
        self.current_task = task_name
        self.current_peak = 0.0

    def check_memory(self) -> float:
        """Get current memory usage in GB (mocked for portability, real impl uses psutil/memory_profiler)."""
        # Mock implementation for validation context
        # In real run, this would use: from memory_profiler import memory_usage
        return 4.5  # Simulated safe usage

    def end_session(self) -> Dict[str, Any]:
        duration = time.time() - self.start_time if self.start_time else 0
        metrics = {
            "task": self.current_task,
            "duration_seconds": duration,
            "peak_ram_gb": self.current_peak,
        }
        self.session_metrics.append(metrics)
        return metrics

# Global instance for session tracking
_monitor = MemoryMonitor()

def measure_memory(func):
    """Decorator to measure memory usage of a function."""
    def wrapper(*args, **kwargs):
        start_mem = _monitor.check_memory()
        result = func(*args, **kwargs)
        end_mem = _monitor.check_memory()
        usage = end_mem - start_mem
        if usage > _monitor.current_peak:
            _monitor.current_peak = usage
        return result
    return wrapper

def check_memory_limit(current_usage_gb: float) -> bool:
    """Check if current usage exceeds the limit."""
    return current_usage_gb > _monitor.limit_gb

def get_session_metrics() -> List[Dict[str, Any]]:
    return _monitor.session_metrics

def clear_session_metrics() -> None:
    _monitor.session_metrics = []

def should_batch_process(current_usage_gb: float, threshold_gb: float = 6.0) -> bool:
    """Determine if batch processing should be triggered."""
    return current_usage_gb > threshold_gb