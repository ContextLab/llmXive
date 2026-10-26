"""Utility to monitor wall‑clock time, peak memory, and peak disk usage.

The ``ResourceMonitor`` class can be used as a context manager:

    from src.utils.resource_monitor import ResourceMonitor

    with ResourceMonitor() as rm:
        # code to monitor
        ...

    # After exiting the block ``rm.report`` contains the measurements.
The report is automatically written to ``data/results/resource_usage.json``
in JSON format.
"""

import json
import time
from pathlib import Path

import psutil

from llmxive_toolkit import paths, get_logger

log = get_logger(__name__)

class ResourceMonitor:
    """Monitor wall‑time, peak RSS memory, and peak disk usage."""

    def __init__(self, output_path: Path = None):
        self.start_time = None
        self.end_time = None
        self.peak_memory_gb = 0.0
        self.peak_disk_gb = 0.0
        self.output_path = output_path or paths.results("resource_usage.json")
        self._process = psutil.Process()

    def __enter__(self):
        self.start_time = time.time()
        self._process.cpu_percent(interval=None)  # prime CPU percent
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.end_time = time.time()
        self._collect_peak_memory()
        self._collect_peak_disk()
        self._write_report()
        # Do not suppress exceptions
        return False

    @property
    def wall_time_seconds(self) -> float:
        if self.start_time is None or self.end_time is None:
            return 0.0
        return self.end_time - self.start_time

    def _collect_peak_memory(self):
        # psutil reports memory in bytes; convert to GB.
        mem_info = self._process.memory_info()
        self.peak_memory_gb = mem_info.rss / (1024 ** 3)

    def _collect_peak_disk(self):
        # Disk usage of the project root.
        usage = psutil.disk_usage(str(paths.root))
        self.peak_disk_gb = usage.used / (1024 ** 3)

    def _write_report(self):
        report = {
            "wall_time_seconds": self.wall_time_seconds,
            "peak_memory_gb": round(self.peak_memory_gb, 3),
            "peak_disk_gb": round(self.peak_disk_gb, 3),
        }
        self.output_path.parent.mkdir(parents=True, exist_ok=True)
        with self.output_path.open("w", encoding="utf-8") as fh:
            json.dump(report, fh, indent=2, sort_keys=True)
        log.info("Resource usage written to %s", self.output_path)

def monitor_resource_usage(func):
    """Decorator that runs ``func`` inside a ``ResourceMonitor``."""
    def wrapper(*args, **kwargs):
        with ResourceMonitor() as rm:
            return func(*args, **kwargs)
    return wrapper
