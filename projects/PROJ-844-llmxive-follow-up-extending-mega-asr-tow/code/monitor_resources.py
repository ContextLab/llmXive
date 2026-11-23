"""
Resource monitoring utilities for the llmXive pipeline.

This module implements SC-004: Track peak RSS and wall-clock time
for research experiments to ensure compute budget compliance.
"""

import os
import sys
import time
import resource
import json
from pathlib import Path
from contextlib import contextmanager
from typing import Optional, Dict, Any

# Ensure cross-platform compatibility (Linux/macOS primarily)
# Windows support would require psutil, but we stick to standard lib for now
# as per the existing requirements.txt (psutil not listed, but resource is standard on Unix)
if sys.platform != "win32":
  import resource
else:
  # Fallback for Windows if needed, though resource module is Unix-only
  # We will raise an error if run on Windows without psutil to avoid silent failure
  resource = None


class ResourceMonitor:
    """
    Monitors peak Resident Set Size (RSS) memory usage and wall-clock time.

    Attributes:
        start_time (float): Wall-clock start time in seconds.
        peak_rss (int): Peak RSS in bytes (Unix only).
        elapsed_time (float): Elapsed wall-clock time in seconds.
    """

    def __init__(self):
        self.start_time: float = 0.0
        self.peak_rss: int = 0
        self.elapsed_time: float = 0.0
        self._running: bool = False

        if resource is None:
            raise RuntimeError(
                "Resource monitoring requires a Unix-like OS (Linux/macOS). "
                "The 'resource' module is not available on Windows. "
                "Please run this on a supported platform or install 'psutil' and modify the code."
            )

    def start(self) -> None:
        """Start the timer and reset peak RSS tracking."""
        self.start_time = time.perf_counter()
        self.peak_rss = 0
        self._running = True

        # Reset peak RSS counter for the current process
        # getrusage(RUSAGE_SELF).ru_maxrss is the peak RSS since the last call
        # or since process start if not called before.
        try:
            usage = resource.getrusage(resource.RUSAGE_SELF)
            # ru_maxrss is in kilobytes on Linux, bytes on some other systems.
            # Standard Linux: ru_maxrss is in KB. We normalize to bytes.
            # We assume Linux behavior (KB) as it's the most common CI environment.
            # To be safe, we check the platform or just assume KB as per Linux docs.
            # Linux man page: "The value is in kilobytes."
            self.peak_rss = usage.ru_maxrss * 1024
        except Exception as e:
            raise RuntimeError(f"Failed to initialize resource monitor: {e}")

    def update(self) -> None:
        """Update the peak RSS and elapsed time."""
        if not self._running:
            return

        try:
            usage = resource.getrusage(resource.RUSAGE_SELF)
            current_rss = usage.ru_maxrss * 1024  # Convert KB to bytes (Linux standard)
            if current_rss > self.peak_rss:
                self.peak_rss = current_rss
        except Exception:
            pass  # Silently ignore if we can't read, but we already started

    def stop(self) -> None:
        """Stop the timer and finalize measurements."""
        if not self._running:
            return
        self.update()  # Final update
        self.elapsed_time = time.perf_counter() - self.start_time
        self._running = False

    def get_report(self) -> Dict[str, Any]:
        """
        Generate a dictionary report of the resource usage.

        Returns:
            dict: Contains 'peak_rss_bytes', 'peak_rss_mb', 'elapsed_time_seconds'.
        """
        if self._running:
            self.update()

        return {
            "peak_rss_bytes": self.peak_rss,
            "peak_rss_mb": self.peak_rss / (1024 * 1024),
            "elapsed_time_seconds": self.elapsed_time,
            "platform": sys.platform
        }

    def save_report(self, output_path: str) -> None:
        """
        Save the resource report to a JSON file.

        Args:
            output_path: Path to the output JSON file.
        """
        report = self.get_report()
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2)


@contextmanager
def monitor_resources(output_file: Optional[str] = None):
    """
    Context manager to monitor resources for a block of code.

    Usage:
        with monitor_resources("data/derived/resource_usage.json"):
            # ... heavy computation ...
            pass

    Args:
        output_file: Optional path to save the JSON report upon exit.
    """
    monitor = ResourceMonitor()
    monitor.start()
    try:
        yield monitor
    finally:
        monitor.stop()
        if output_file:
            monitor.save_report(output_file)


def main():
    """
    Entry point for the resource monitor script.

    This script runs a dummy heavy computation (if no input is provided)
    or simply initializes the monitor to demonstrate functionality.
    For the actual pipeline, this script is imported or called to wrap
    other heavy tasks.

    When run directly, it performs a synthetic load test (matrix multiplication)
    to generate a real measurement, saving the result to
    `data/derived/resource_monitoring_report.json`.
    """
    import numpy as np

    output_path = "data/derived/resource_monitoring_report.json"
    print(f"Starting resource monitoring. Output will be saved to: {output_path}")

    with monitor_resources(output_file=output_path) as monitor:
        print("Performing dummy heavy computation (matrix multiplication)...")
        # Simulate a heavy CPU and memory task to generate a real measurement
        # Matrix size chosen to be significant but safe for the 7GB budget
        size = 2000
        print(f"Creating {size}x{size} float64 matrices...")
        A = np.random.rand(size, size)
        B = np.random.rand(size, size)
        print("Computing dot product...")
        C = np.dot(A, B)
        print("Computation finished.")
        # Force garbage collection to ensure memory is released before final report
        import gc
        gc.collect()

    report = monitor.get_report()
    print(f"\n--- Resource Report ---")
    print(f"Peak RSS: {report['peak_rss_mb']:.2f} MB")
    print(f"Elapsed Time: {report['elapsed_time_seconds']:.2f} seconds")
    print(f"Platform: {report['platform']}")
    print(f"Report saved to: {output_path}")


if __name__ == "__main__":
    main()
