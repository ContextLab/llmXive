import time
import json
from contextlib import contextmanager
from typing import Dict, Any, Optional, List

import psutil
import os


def get_ram_usage_mb() -> float:
    """Get current RAM usage in MB."""
    process = psutil.Process(os.getpid())
    return process.memory_info().rss / (1024 * 1024)


def get_cpu_utilization() -> float:
    """Get current CPU utilization percentage."""
    return psutil.cpu_percent(interval=0.1)


def get_system_ram_usage_mb() -> float:
    """Get system RAM usage in MB."""
    return psutil.virtual_memory().used / (1024 * 1024)


def get_system_cpu_utilization() -> float:
    """Get system CPU utilization percentage."""
    return psutil.cpu_percent(interval=1)


@contextmanager
def track_inference_time():
    """Context manager to track inference time."""
    start = time.time()
    try:
        yield
    finally:
        end = time.time()
        logging.getLogger(__name__).info(f"Inference time: {end - start:.4f}s")


def capture_snapshot() -> Dict[str, Any]:
    """Capture a snapshot of current system resources."""
    return {
        "ram_mb": get_ram_usage_mb(),
        "cpu_percent": get_cpu_utilization(),
        "timestamp": time.time()
    }


def record_batch_metrics(
    batch_id: int,
    time_seconds: float,
    items: int,
    ram_mb: Optional[float] = None,
    cpu_percent: Optional[float] = None
) -> Dict[str, Any]:
    """Record metrics for a batch."""
    if ram_mb is None:
        ram_mb = get_ram_usage_mb()
    if cpu_percent is None:
        cpu_percent = get_cpu_utilization()

    return {
        "batch_id": batch_id,
        "time_seconds": time_seconds,
        "items": items,
        "ram_mb": ram_mb,
        "cpu_percent": cpu_percent,
        "timestamp": time.time()
    }


def save_metrics_to_file(metrics: List[Dict[str, Any]], output_path: str) -> None:
    """Save metrics to a JSON file."""
    with open(output_path, "w") as f:
        json.dump(metrics, f, indent=2)


def get_peak_ram_for_batch(batch_metrics: List[Dict[str, Any]]) -> float:
    """Get peak RAM usage from a list of batch metrics."""
    if not batch_metrics:
        return 0.0
    return max(m.get("ram_mb", 0) for m in batch_metrics)
