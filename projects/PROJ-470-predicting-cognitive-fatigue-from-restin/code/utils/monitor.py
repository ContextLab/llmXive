"""
Monitoring infrastructure for resource usage.
"""
from __future__ import annotations

import json
import os
import time
from datetime import datetime
from typing import Any, Dict

try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False


class ResourceMonitor:
    """Monitor resource usage (memory, runtime)."""

    def __init__(self):
        self.start_time: float | None = None
        self.end_time: float | None = None
        self.peak_memory_mb: float = 0.0
        self.process = None

        if HAS_PSUTIL:
            self.process = psutil.Process()

    def start(self):
        """Start monitoring."""
        self.start_time = time.time()
        if self.process:
            # Get initial memory
            self.peak_memory_mb = self.process.memory_info().rss / (1024 * 1024)

    def stop(self):
        """Stop monitoring and calculate totals."""
        self.end_time = time.time()
        if self.process:
            # Update peak memory
            current_memory = self.process.memory_info().rss / (1024 * 1024)
            if current_memory > self.peak_memory_mb:
                self.peak_memory_mb = current_memory

    def get_stats(self) -> Dict[str, Any]:
        """Get monitoring statistics."""
        if self.start_time is None or self.end_time is None:
            return {
                "peak_rss_gb": 0.0,
                "total_runtime_hours": 0.0
            }
        
        runtime_hours = (self.end_time - self.start_time) / 3600
        peak_rss_gb = self.peak_memory_mb / 1024
        
        return {
            "peak_rss_gb": round(peak_rss_gb, 4),
            "total_runtime_hours": round(runtime_hours, 4)
        }

    def save_stats(self, filepath: str = "data/analysis/resource_usage.json"):
        """Save statistics to a JSON file."""
        stats = self.get_stats()
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, 'w') as f:
            json.dump(stats, f, indent=2)


_MONITOR: ResourceMonitor | None = None


def get_peak_memory_mb() -> float:
    """Get the current peak memory usage in MB."""
    global _MONITOR
    if _MONITOR is None:
        return 0.0
    return _MONITOR.peak_memory_mb


def run_stage_with_memory(func):
    """Decorator to run a function with memory monitoring."""
    def wrapper(*args, **kwargs):
        global _MONITOR
        if _MONITOR is None:
            _MONITOR = ResourceMonitor()
        
        _MONITOR.start()
        try:
            result = func(*args, **kwargs)
        finally:
            _MONITOR.stop()
            _MONITOR.save_stats()
        return result
    return wrapper


def main():
    """Entry point for standalone monitoring."""
    monitor = ResourceMonitor()
    monitor.start()
    # Simulate some work
    time.sleep(1)
    monitor.stop()
    monitor.save_stats()
    print(f"Peak memory: {monitor.peak_memory_mb:.2f} MB")
    print(f"Runtime: {(monitor.end_time - monitor.start_time):.2f} seconds")


if __name__ == "__main__":
    main()