"""
Resource monitoring utilities for the LLM code smell detection pipeline.

This module provides functions to capture RAM usage, CPU utilization, and
inference time using psutil, intended for use within inference loops
to track resource consumption during batch processing.
"""
import time
import json
from contextlib import contextmanager
from typing import Dict, Any, Optional, List

import psutil
import os


# Initialize process object once to avoid repeated overhead
_process = psutil.Process(os.getpid())


def get_ram_usage_mb() -> float:
    """
    Get current RAM usage of the current process in Megabytes.

    Returns:
        float: Current RSS (Resident Set Size) memory usage in MB.
    """
    mem_info = _process.memory_info()
    return mem_info.rss / (1024 * 1024)


def get_cpu_utilization() -> float:
    """
    Get current CPU utilization of the current process as a percentage.

    Returns:
        float: CPU usage percentage (0.0 to 100.0 * num_cpus).
    """
    return _process.cpu_percent(interval=None)


def get_system_ram_usage_mb() -> float:
    """
    Get total system RAM usage in Megabytes.

    Returns:
        float: Total system RAM usage in MB.
    """
    mem_info = psutil.virtual_memory()
    return mem_info.used / (1024 * 1024)


def get_system_cpu_utilization() -> float:
    """
    Get total system CPU utilization as a percentage.

    Returns:
        float: System-wide CPU usage percentage.
    """
    return psutil.cpu_percent(interval=None)


def capture_snapshot() -> Dict[str, Any]:
    """
    Capture a snapshot of current resource metrics.

    Returns:
        dict: A dictionary containing:
            - 'timestamp': Unix timestamp
            - 'process_ram_mb': Current process RAM usage in MB
            - 'process_cpu_pct': Current process CPU percentage
            - 'system_ram_mb': Current system RAM usage in MB
            - 'system_cpu_pct': Current system CPU percentage
    """
    return {
        "timestamp": time.time(),
        "process_ram_mb": get_ram_usage_mb(),
        "process_cpu_pct": get_cpu_utilization(),
        "system_ram_mb": get_system_ram_usage_mb(),
        "system_cpu_pct": get_system_cpu_utilization(),
    }


@contextmanager
def track_inference_time():
    """
    Context manager to track inference time and resource usage.

    Yields a dictionary that will be populated with timing and resource
    metrics upon exiting the context.

    Example:
        with track_inference_time() as metrics:
            # perform inference
            pass
        print(metrics['duration_seconds'])
    """
    start_time = time.time()
    start_ram = get_ram_usage_mb()
    start_cpu = get_cpu_utilization()

    snapshot_start = capture_snapshot()

    yield {
        "start_timestamp": snapshot_start["timestamp"],
        "start_process_ram_mb": snapshot_start["process_ram_mb"],
        "start_process_cpu_pct": snapshot_start["process_cpu_pct"],
    }

    end_time = time.time()
    end_ram = get_ram_usage_mb()
    end_cpu = get_cpu_utilization()

    snapshot_end = capture_snapshot()

    # Update the yielded dict with final metrics
    metrics = {
        "start_timestamp": snapshot_start["timestamp"],
        "end_timestamp": snapshot_end["timestamp"],
        "duration_seconds": end_time - start_time,
        "start_process_ram_mb": snapshot_start["process_ram_mb"],
        "end_process_ram_mb": snapshot_end["process_ram_mb"],
        "peak_process_ram_mb": max(snapshot_start["process_ram_mb"], snapshot_end["process_ram_mb"]),
        "ram_delta_mb": end_ram - start_ram,
        "start_process_cpu_pct": snapshot_start["process_cpu_pct"],
        "end_process_cpu_pct": snapshot_end["process_cpu_pct"],
        "start_system_ram_mb": snapshot_start["system_ram_mb"],
        "end_system_ram_mb": snapshot_end["system_ram_mb"],
        "start_system_cpu_pct": snapshot_start["system_cpu_pct"],
        "end_system_cpu_pct": snapshot_end["system_cpu_pct"],
    }


def record_batch_metrics(batch_id: int, metrics: Dict[str, Any]) -> Dict[str, Any]:
    """
    Record metrics for a specific batch of inference.

    Args:
        batch_id: The identifier for the batch.
        metrics: The metrics dictionary from track_inference_time context.

    Returns:
        dict: A record suitable for JSON serialization containing
              batch ID and all metrics.
    """
    record = {
        "batch_id": batch_id,
        "timestamp": time.time(),
        **metrics
    }
    return record


def save_metrics_to_file(records: List[Dict[str, Any]], output_path: str) -> None:
    """
    Save a list of metric records to a JSON file.

    Args:
        records: List of metric dictionaries to save.
        output_path: Path to the output JSON file.
    """
    import json
    import os

    # Ensure directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(records, f, indent=2)


def get_peak_ram_for_batch(records: List[Dict[str, Any]], batch_id: int) -> Optional[float]:
    """
    Retrieve the peak RAM usage for a specific batch from recorded metrics.

    Args:
        records: List of metric records.
        batch_id: The batch ID to look up.

    Returns:
        float or None: Peak RAM in MB, or None if batch not found.
    """
    for record in records:
        if record.get("batch_id") == batch_id:
            return record.get("peak_process_ram_mb")
    return None
