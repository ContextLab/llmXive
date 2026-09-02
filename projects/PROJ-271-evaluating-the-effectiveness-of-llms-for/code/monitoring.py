import time
import json
from contextlib import contextmanager
from typing import Dict, Any, Optional, List
import psutil
import os
import logging

from config import get_results_path, setup_logging

logger = logging.getLogger(__name__)

def get_ram_usage_mb() -> float:
    """Returns current RAM usage in MB."""
    process = psutil.Process(os.getpid())
    return process.memory_info().rss / (1024 * 1024)

def get_cpu_utilization() -> float:
    """Returns current CPU utilization percentage."""
    return psutil.cpu_percent(interval=0.1)

def get_system_ram_usage_mb() -> float:
    """Returns total system RAM usage in MB."""
    return psutil.virtual_memory().used / (1024 * 1024)

def get_system_cpu_utilization() -> float:
    """Returns total system CPU utilization percentage."""
    return psutil.cpu_percent(interval=0.1)

@contextmanager
def track_inference_time():
    """Context manager to track inference time."""
    start = time.time()
    try:
        yield
    finally:
        end = time.time()
        logger.info(f"Inference took {end - start:.2f} seconds")

def capture_snapshot() -> Dict[str, Any]:
    """Captures a snapshot of system resources."""
    return {
        "ram_mb": get_ram_usage_mb(),
        "cpu_util": get_cpu_utilization(),
        "system_ram_mb": get_system_ram_usage_mb(),
        "system_cpu_util": get_system_cpu_utilization()
    }

def record_batch_metrics(batch_id: int, metrics: Dict[str, Any], output_file: str):
    """Records batch-level metrics to a JSON file."""
    record = {
        "batch_id": batch_id,
        "timestamp": time.time(),
        **metrics
    }
    
    try:
        with open(output_file, "r") as f:
            data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        data = []
    
    data.append(record)
    
    with open(output_file, "w") as f:
        json.dump(data, f, indent=2)

def save_metrics_to_file(metrics: List[Dict[str, Any]], output_file: str):
    """Saves a list of metrics to a JSON file."""
    with open(output_file, "w") as f:
        json.dump(metrics, f, indent=2)

def get_peak_ram_for_batch(batch_metrics: List[Dict[str, Any]]) -> float:
    """Calculates peak RAM usage from a list of batch metrics."""
    if not batch_metrics:
        return 0.0
    return max(m.get("ram_mb", 0) for m in batch_metrics)
