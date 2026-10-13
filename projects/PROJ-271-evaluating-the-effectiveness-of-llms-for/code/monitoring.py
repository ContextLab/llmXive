"""
Monitoring utilities for recording resource usage per batch.

This module provides functions to:
- Query current RAM and CPU usage.
- Capture a snapshot of resource usage before and after a block of code.
- Record per‑batch metrics (batch index, size, elapsed time, RAM, CPU).
- Persist the collected metrics to ``results/resource_metrics.json``.

The implementation is deliberately lightweight and has no external
dependencies beyond the Python standard library and ``psutil`` (already
available in the environment).  It matches the public API surface
declared in the project specification and is compatible with the rest
of the code base (e.g. ``semantic_analysis.py``).
"""

import json
import os
import time
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import psutil

from config import get_results_path

# ----------------------------------------------------------------------
# Global state
# ----------------------------------------------------------------------
# A list that accumulates metric dictionaries for each processed batch.
_metrics_log: List[Dict[str, Any]] = []

# Tracks the highest RAM usage observed across all batches (in MB).
_peak_ram_mb: float = 0.0


# ----------------------------------------------------------------------
# Basic resource queries
# ----------------------------------------------------------------------
def get_ram_usage_mb() -> float:
    """Return the current RAM usage of this Python process (MiB)."""
    process = psutil.Process(os.getpid())
    return process.memory_info().rss / (1024 * 1024)


def get_cpu_utilization() -> float:
    """Return the current CPU utilization percentage for this process."""
    # ``interval=0.1`` gives an instantaneous snapshot without blocking long.
    return psutil.cpu_percent(interval=0.1)


def get_system_ram_usage_mb() -> float:
    """Return the total system RAM currently in use (MiB)."""
    return psutil.virtual_memory().used / (1024 * 1024)


def get_system_cpu_utilization() -> float:
    """Return the overall system CPU utilization percentage."""
    return psutil.cpu_percent(interval=0.1)


# ----------------------------------------------------------------------
# Helper decorators / context managers
# ----------------------------------------------------------------------
def track_inference_time(func):
    """
    Decorator that measures the execution time of ``func``.

    The wrapped function returns a tuple ``(result, elapsed_seconds)``.
    """
    def wrapper(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        elapsed = time.time() - start
        return result, elapsed
    return wrapper


@contextmanager
def capture_snapshot() -> Dict[str, float]:
    """
    Context manager that records RAM, CPU and wall‑clock time before and
    after the enclosed block.

    Example
    -------
    >>> with capture_snapshot() as snap:
    ...     heavy_computation()
    >>> print(snap)   # contains start_/end_ keys and ``duration_sec``
    """
    snapshot: Dict[str, float] = {
        "start_ram_mb": get_ram_usage_mb(),
        "start_cpu_pct": get_cpu_utilization(),
        "start_time": time.time(),
    }
    # Yield the dict so callers can inspect/augment it if they wish.
    yield snapshot
    # After the block, enrich the dict with end measurements.
    snapshot.update({
        "end_ram_mb": get_ram_usage_mb(),
        "end_cpu_pct": get_cpu_utilization(),
        "duration_sec": time.time() - snapshot["start_time"],
    })


# ----------------------------------------------------------------------
# Batch‑level recording
# ----------------------------------------------------------------------
def record_batch_metrics(
    batch_idx: int,
    batch_size: int,
    time_sec: float,
    ram_mb: float,
    cpu_pct: float,
) -> None:
    """
    Record metrics for a single batch and update the global log.

    Parameters
    ----------
    batch_idx: int
        Zero‑based index of the processed batch.
    batch_size: int
        Number of functions/items in the batch.
    time_sec: float
        Elapsed time for the batch (seconds).
    ram_mb: float
        Peak RAM usage observed during the batch (MiB).
    cpu_pct: float
        Average CPU utilization during the batch (percentage).
    """
    global _peak_ram_mb
    if ram_mb > _peak_ram_mb:
        _peak_ram_mb = ram_mb

    entry = {
        "batch_idx": batch_idx,
        "batch_size": batch_size,
        "time_sec": time_sec,
        "ram_mb": ram_mb,
        "cpu_pct": cpu_pct,
        "timestamp": time.time(),
    }
    _metrics_log.append(entry)


def get_peak_ram_for_batch() -> float:
    """Return the highest RAM usage observed across all recorded batches."""
    return _peak_ram_mb


# ----------------------------------------------------------------------
# Persistence
# ----------------------------------------------------------------------
def save_metrics_to_file(
    data: Optional[Union[Dict[str, Any], List[Dict[str, Any]]]] = None,
    path: Optional[Union[str, Path]] = None,
    append: bool = False,
) -> None:
    """
    Serialize the collected metrics to JSON.

    If ``data`` is provided, it is written (or appended) to the target
    file.  When ``data`` is ``None``, the function writes the internal
    ``_metrics_log`` list.

    Parameters
    ----------
    data: dict or list of dicts, optional
        Metric(s) to write.  If omitted, the global log is persisted.
    path: str or Path, optional
        Destination file.  Defaults to ``results/resource_metrics.json``.
    append: bool, default False
        When True and the file already exists, the new data are merged
        with the existing JSON array; otherwise the file is overwritten.
    """
    if path is None:
        dest_path = get_results_path("resource_metrics.json")
    else:
        dest_path = Path(path)

    # Ensure the parent directory exists.
    dest_path.parent.mkdir(parents=True, exist_ok=True)

    # Determine what we are about to write.
    if data is None:
        payload = _metrics_log
    else:
        payload = data

    # Normalise payload to a list – the JSON file is always an array.
    if isinstance(payload, dict):
        payload = [payload]

    if append and dest_path.exists():
        try:
            with dest_path.open("r", encoding="utf-8") as f:
                existing = json.load(f)
            if not isinstance(existing, list):
                existing = [existing]
        except Exception:
            existing = []
        combined = existing + payload
    else:
        combined = payload

    with dest_path.open("w", encoding="utf-8") as f:
        json.dump(combined, f, indent=2, ensure_ascii=False)


# ----------------------------------------------------------------------
# Convenience wrapper used by other modules
# ----------------------------------------------------------------------
def record_and_persist_batch(
    batch_idx: int,
    batch_size: int,
    time_sec: float,
    ram_mb: float,
    cpu_pct: float,
) -> None:
    """
    Record a batch's metrics and immediately persist the updated log.
    This helper matches the pattern used in ``semantic_analysis.py``.
    """
    record_batch_metrics(batch_idx, batch_size, time_sec, ram_mb, cpu_pct)
    # Persist the full log after each batch – lightweight for the small
    # number of batches typical in this project.
    save_metrics_to_file()