"""
CPU Utilization Monitoring Module for llmXive.

This module provides functionality to monitor CPU utilization using psutil
and log metrics at the same frequency as the base logging infrastructure (T005a).
It integrates with the experiment logging system to record resource usage.
"""

import os
import time
import json
import psutil
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime

# Ensure the data directory exists
DATA_PROCESSED_DIR = Path(os.environ.get("DATA_PROCESSED_DIR", "data/processed"))
LOG_FILE_PATH = DATA_PROCESSED_DIR / "experiment.log"

# Ensure the directory exists
DATA_PROCESSED_DIR.mkdir(parents=True, exist_ok=True)


class CPUMonitor:
    """
    Monitors CPU utilization for the current process and system-wide.
    Records metrics to the experiment log file in JSON format.
    """

    def __init__(self, log_path: Optional[Path] = None, interval: float = 1.0):
        """
        Initialize the CPU monitor.

        Args:
            log_path: Path to the log file. Defaults to data/processed/experiment.log.
            interval: Time interval in seconds between measurements.
        """
        self.log_path = log_path or LOG_FILE_PATH
        self.interval = interval
        self.process = psutil.Process(os.getpid())
        # Initialize the log file if it doesn't exist
        if not self.log_path.exists():
            with open(self.log_path, 'w') as f:
                f.write('')  # Create empty file

        # Ensure the process CPU times are initialized
        self.process.cpu_percent()

    def get_cpu_metrics(self) -> Dict[str, Any]:
        """
        Collect current CPU metrics.

        Returns:
            Dictionary containing CPU metrics.
        """
        # Get process-specific CPU percent (interval-based)
        process_cpu = self.process.cpu_percent(interval=None)

        # Get system-wide CPU percent
        system_cpu = psutil.cpu_percent(interval=None)

        # Get number of CPU cores
        cpu_count = psutil.cpu_count()

        # Get CPU frequency if available
        cpu_freq = None
        freq_info = psutil.cpu_freq()
        if freq_info:
            cpu_freq = {
                "current": freq_info.current,
                "min": freq_info.min,
                "max": freq_info.max
            }

        # Get CPU times
        cpu_times = self.process.cpu_times()

        return {
            "timestamp": datetime.utcnow().isoformat(),
            "process_cpu_percent": process_cpu,
            "system_cpu_percent": system_cpu,
            "cpu_count": cpu_count,
            "cpu_frequency": cpu_freq,
            "user_time": cpu_times.user,
            "system_time": cpu_times.system,
            "pid": self.process.pid
        }

    def log_step(self, step_id: str, extra_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Log CPU metrics for a specific execution step.

        Args:
            step_id: Identifier for the current execution step.
            extra_data: Optional additional data to include in the log entry.

        Returns:
            The logged metrics dictionary.
        """
        metrics = self.get_cpu_metrics()
        metrics["step_id"] = step_id

        if extra_data:
            metrics.update(extra_data)

        # Append to log file as JSON lines
        with open(self.log_path, 'a') as f:
            f.write(json.dumps(metrics) + '\n')

        return metrics

    def start_monitoring(self, step_id: str, duration: float, sample_interval: Optional[float] = None) -> List[Dict[str, Any]]:
        """
        Start monitoring CPU for a specific duration.

        Args:
            step_id: Identifier for the execution step.
            duration: Total duration to monitor in seconds.
            sample_interval: Interval between samples. Defaults to self.interval.

        Returns:
            List of all collected metrics dictionaries.
        """
        if sample_interval is None:
            sample_interval = self.interval

        start_time = time.time()
        end_time = start_time + duration
        samples = []

        # Initialize CPU percent calculation
        self.process.cpu_percent()

        while time.time() < end_time:
            metrics = self.get_cpu_metrics()
            metrics["step_id"] = step_id
            metrics["elapsed_time"] = time.time() - start_time
            samples.append(metrics)

            # Write to log file
            with open(self.log_path, 'a') as f:
                f.write(json.dumps(metrics) + '\n')

            time.sleep(sample_interval)

        return samples


def monitor_cpu_for_step(
    step_id: str,
    duration: Optional[float] = None,
    interval: float = 1.0,
    extra_data: Optional[Dict[str, Any]] = None
) -> Dict[str, Any] | List[Dict[str, Any]]:
    """
    Convenience function to monitor CPU for a single step.

    Args:
        step_id: Identifier for the execution step.
        duration: If provided, monitor for this duration and return a list of samples.
                 If None, take a single snapshot and return a dict.
        interval: Sampling interval in seconds (used if duration is provided).
        extra_data: Optional additional data to include in the log entry.

    Returns:
        Single metrics dict (if duration is None) or list of dicts (if duration is provided).
    """
    monitor = CPUMonitor(interval=interval)

    if duration is not None:
        return monitor.start_monitoring(step_id, duration, interval)
    else:
        return monitor.log_step(step_id, extra_data)


def main():
    """
    Main entry point for testing the CPU monitor.
    Runs a simple workload and logs CPU metrics.
    """
    import sys

    print("Starting CPU Monitor Test...")

    # Create a monitor instance
    monitor = CPUMonitor()

    # Log a single step
    print("Logging single step...")
    single_metrics = monitor.log_step("test_single_step", {"workload": "initialization"})
    print(f"Single step metrics: {json.dumps(single_metrics, indent=2)}")

    # Simulate a workload and monitor continuously
    print("Starting continuous monitoring for 5 seconds...")
    samples = monitor.start_monitoring(
        "test_continuous_workload",
        duration=5.0,
        sample_interval=0.5
    )

    print(f"Collected {len(samples)} samples.")
    print(f"Average system CPU: {sum(s['system_cpu_percent'] for s in samples) / len(samples):.2f}%")
    print(f"Average process CPU: {sum(s['process_cpu_percent'] for s in samples) / len(samples):.2f}%")

    # Verify log file was written
    if monitor.log_path.exists():
        log_size = monitor.log_path.stat().st_size
        print(f"Log file written successfully: {monitor.log_path} ({log_size} bytes)")
    else:
        print("ERROR: Log file was not created!")
        sys.exit(1)

    print("CPU Monitor Test completed successfully.")


if __name__ == "__main__":
    main()