import time
import json
from contextlib import contextmanager
from typing import Dict, Any, Optional, List
import psutil
import os

from config import get_results_path

# Global peak tracker
_peak_ram_mb = 0.0
_metrics_log: List[Dict[str, Any]] = []

def get_ram_usage_mb() -> float:
    """Get current RAM usage in MB."""
    process = psutil.Process(os.getpid())
    return process.memory_info().rss / 1024 / 1024

def get_cpu_utilization() -> float:
    """Get current CPU utilization percentage."""
    return psutil.cpu_percent(interval=0.1)

def get_system_ram_usage_mb() -> float:
    """Get total system RAM usage."""
    return psutil.virtual_memory().used / 1024 / 1024

def get_system_cpu_utilization() -> float:
    """Get total system CPU utilization."""
    return psutil.cpu_percent(interval=0.1)

def track_inference_time(func):
    """Decorator to track execution time."""
    def wrapper(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        end = time.time()
        return result, end - start
    return wrapper

@contextmanager
def capture_snapshot():
    """Context manager to capture start/end snapshots."""
    start_ram = get_ram_usage_mb()
    start_cpu = get_cpu_utilization()
    start_time = time.time()
    yield
    end_ram = get_ram_usage_mb()
    end_cpu = get_cpu_utilization()
    end_time = time.time()
    return {
        "start_ram_mb": start_ram,
        "end_ram_mb": end_ram,
        "start_cpu_pct": start_cpu,
        "end_cpu_pct": end_cpu,
        "duration_sec": end_time - start_time
    }

def record_batch_metrics(batch_idx: int, batch_size: int, time_sec: float, ram_mb: float, cpu_pct: float):
    """Record metrics for a specific batch."""
    global _peak_ram_mb
    if ram_mb > _peak_ram_mb:
        _peak_ram_mb = ram_mb
    
    entry = {
        "batch_idx": batch_idx,
        "batch_size": batch_size,
        "time_sec": time_sec,
        "ram_mb": ram_mb,
        "cpu_pct": cpu_pct
    }
    _metrics_log.append(entry)

def save_metrics_to_file(data: Dict[str, Any], path: Optional[str] = None):
    """Save metrics dictionary to a JSON file."""
    if path is None:
        path = get_results_path("resource_metrics.json")
    else:
        path = Path(path)
    
    # Ensure directory exists
    path.parent.mkdir(parents=True, exist_ok=True)
    
    # If data is a list (batch metrics), append or overwrite? 
    # For simplicity, we overwrite the file with the provided data structure.
    # If the file exists and we want to append, logic would be more complex.
    # Given the task requirements, we write the specific report or append to a log.
    # Here we assume 'data' is the specific report to save (like sample_report).
    # For batch metrics, we might want to append to a running log.
    
    if isinstance(data, list) and path.name == "resource_metrics.json":
        # If saving batch metrics, load existing and append
        existing = []
        if path.exists():
            try:
                with open(path, 'r') as f:
                    existing = json.load(f)
            except:
                existing = []
        existing.extend(data)
        with open(path, 'w') as f:
            json.dump(existing, f, indent=2)
    else:
        with open(path, 'w') as f:
            json.dump(data, f, indent=2)

def get_peak_ram_for_batch() -> float:
    """Get the peak RAM observed so far."""
    return _peak_ram_mb
