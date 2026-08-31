import time
import json
from contextlib import contextmanager
from typing import Dict, Any, Optional, List
import psutil
import os

# Global tracking variables
peak_ram_mb = 0.0
batch_metrics: List[Dict[str, Any]] = []

def get_ram_usage_mb() -> float:
    """Get current RAM usage in MB for the current process."""
    process = psutil.Process(os.getpid())
    return process.memory_info().rss / (1024 * 1024)

def get_cpu_utilization() -> float:
    """Get current CPU utilization percentage."""
    return psutil.cpu_percent(interval=0.1)

def get_system_ram_usage_mb() -> float:
    """Get total system RAM usage in MB."""
    return psutil.virtual_memory().used / (1024 * 1024)

def get_system_cpu_utilization() -> float:
    """Get total system CPU utilization percentage."""
    return psutil.cpu_percent(interval=0.1)

@contextmanager
def track_inference_time(batch_id: int):
    """Context manager to track inference time for a batch."""
    start = time.time()
    try:
        yield
    finally:
        end = time.time()
        duration = end - start
        batch_metrics.append({
            "batch_id": batch_id,
            "duration_seconds": duration,
            "timestamp": time.time()
        })

def capture_snapshot() -> Dict[str, float]:
    """Capture a snapshot of system resources."""
    return {
        "ram_mb": get_ram_usage_mb(),
        "cpu_util": get_cpu_utilization(),
        "system_ram_mb": get_system_ram_usage_mb(),
        "system_cpu_util": get_system_cpu_utilization()
    }

def record_batch_metrics(batch_id: int, metrics: Dict[str, Any]) -> None:
    """Record metrics for a specific batch."""
    snapshot = capture_snapshot()
    batch_metrics.append({
        "batch_id": batch_id,
        "ram_mb": snapshot["ram_mb"],
        "cpu_util": snapshot["cpu_util"],
        "system_ram_mb": snapshot["system_ram_mb"],
        "system_cpu_util": snapshot["system_cpu_util"],
        **metrics
    })

def save_metrics_to_file(output_path: str) -> None:
    """Save collected metrics to a JSON file."""
    with open(output_path, "w") as f:
        json.dump(batch_metrics, f, indent=2)

def get_peak_ram_for_batch() -> float:
    """Get the peak RAM usage observed across all batches."""
    if not batch_metrics:
        return 0.0
    return max(m.get("ram_mb", 0) for m in batch_metrics)