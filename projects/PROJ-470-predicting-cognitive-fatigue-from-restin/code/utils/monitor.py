"""Resource monitoring utilities for pipeline execution.

This module provides cross-platform memory tracking using psutil and
runtime measurement using the time module. It captures peak RSS memory
usage and total runtime during pipeline execution.
"""
from __future__ import annotations

import json
import os
import time
from datetime import datetime
from typing import Any, Dict
import psutil
import threading


class ResourceMonitor:
    """Monitor resource usage (memory, runtime) during pipeline execution."""

    def __init__(self) -> None:
        self.process = psutil.Process(os.getpid())
        self.start_time: float | None = None
        self.end_time: float | None = None
        self.peak_memory_bytes: int = 0
        self._monitoring = False
        self._monitor_thread: threading.Thread | None = None

    def start(self) -> None:
        """Start monitoring resource usage."""
        self.start_time = time.time()
        self._monitoring = True
        self._monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self._monitor_thread.start()

    def stop(self) -> None:
        """Stop monitoring resource usage."""
        self._monitoring = False
        if self._monitor_thread:
            self._monitor_thread.join(timeout=1.0)
        self.end_time = time.time()
        # Final memory check
        current_memory = self.process.memory_info().rss
        if current_memory > self.peak_memory_bytes:
            self.peak_memory_bytes = current_memory

    def _monitor_loop(self) -> None:
        """Background loop to track peak memory usage."""
        while self._monitoring:
            try:
                current_memory = self.process.memory_info().rss
                if current_memory > self.peak_memory_bytes:
                    self.peak_memory_bytes = current_memory
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                break
            time.sleep(0.1)

    def get_peak_memory_gb(self) -> float:
        """Get peak memory usage in gigabytes."""
        return self.peak_memory_bytes / (1024 ** 3)

    def get_total_runtime_hours(self) -> float:
        """Get total runtime in hours."""
        if self.start_time is None:
            return 0.0
        end = self.end_time if self.end_time is not None else time.time()
        duration_seconds = end - self.start_time
        return duration_seconds / 3600.0


def get_peak_memory_mb() -> float:
    """Get current peak memory usage in megabytes for the current process."""
    process = psutil.Process(os.getpid())
    return process.memory_info().rss / (1024 ** 2)


def run_stage_with_memory(stage_name: str, func: Any, *args: Any, **kwargs: Any) -> Any:
    """Run a function stage with memory monitoring."""
    monitor = ResourceMonitor()
    monitor.start()
    try:
        result = func(*args, **kwargs)
        return result
    finally:
        monitor.stop()
        usage = {
            "stage": stage_name,
            "peak_memory_gb": monitor.get_peak_memory_gb(),
            "runtime_hours": monitor.get_total_runtime_hours(),
            "timestamp": datetime.utcnow().isoformat()
        }
        # Log usage to console for debugging
        print(f"Stage {stage_name} completed: {usage}")


def main() -> None:
    """Main entry point for standalone monitoring test.

    This function demonstrates the monitoring capabilities by running a
    simple workload and writing the resource usage to a JSON file.
    """
    monitor = ResourceMonitor()
    monitor.start()

    # Simulate some work
    time.sleep(1)
    _ = [i * i for i in range(1000000)]

    monitor.stop()

    usage = {
        "peak_rss_gb": monitor.get_peak_memory_gb(),
        "total_runtime_hours": monitor.get_total_runtime_hours()
    }

    output_path = "data/analysis/resource_usage.json"
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(usage, f, indent=2)

    print(f"Resource usage: {usage}")
    print(f"Written to: {output_path}")


if __name__ == "__main__":
    main()