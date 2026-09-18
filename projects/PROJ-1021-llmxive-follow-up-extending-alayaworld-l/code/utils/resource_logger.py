"""
Deterministic logging and resource metering utility.

This module provides tools to track RAM usage and wall-clock time for experiments,
ensuring reproducibility and adherence to resource constraints (FR-005).
"""

import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, TextIO

import psutil

# Ensure the utils directory is importable if run as a script
try:
    from . import __file__ as _dummy
except ImportError:
    pass

# Constants
RAM_LIMIT_MB = 7000  # 7 GB limit per FR-005 / US3
TIME_LIMIT_SECONDS = 1800  # 30 minutes per FR-005 / US3


class ResourceMonitor:
    """
    Monitors RAM usage and wall-clock time for a specific process or sequence.
    """

    def __init__(self, sequence_id: str, log_dir: str = "data/logs"):
        """
        Initialize the monitor.

        Args:
            sequence_id: Unique identifier for the sequence being tracked.
            log_dir: Directory to store real-time logs.
        """
        self.sequence_id = sequence_id
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)

        self.process = psutil.Process(os.getpid())
        self.start_time: Optional[float] = None
        self.end_time: Optional[float] = None
        self.peak_ram_mb: float = 0.0
        self.ram_samples: List[float] = []
        self.timestamps: List[float] = []
        self.is_monitoring: bool = False
        self.log_file_path: Optional[Path] = None

    def start(self) -> None:
        """Start the monitoring timer and begin sampling RAM."""
        if self.is_monitoring:
            raise RuntimeError("Monitor is already running.")

        self.start_time = time.time()
        self.is_monitoring = True
        self.peak_ram_mb = 0.0
        self.ram_samples = []
        self.timestamps = []

        # Define log file path
        timestamp_str = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        self.log_file_path = self.log_dir / f"realtime_seq_{self.sequence_id}_{timestamp_str}.json"

        # Initialize log file with header
        initial_log = {
            "sequence_id": self.sequence_id,
            "start_time": datetime.now(timezone.utc).isoformat(),
            "status": "running",
            "samples": []
        }
        with open(self.log_file_path, "w") as f:
            json.dump(initial_log, f, indent=2)

    def _sample_ram(self) -> None:
        """Sample current RAM usage and update peak."""
        try:
            # RSS (Resident Set Size) in bytes
            mem_info = self.process.memory_info()
            current_ram_mb = mem_info.rss / (1024 * 1024)

            self.ram_samples.append(current_ram_mb)
            self.timestamps.append(time.time() - self.start_time if self.start_time else 0)

            if current_ram_mb > self.peak_ram_mb:
                self.peak_ram_mb = current_ram_mb
        except psutil.NoSuchProcess:
            pass  # Process might have terminated

    def record_step(self, step_data: Optional[Dict[str, Any]] = None) -> None:
        """
        Record a step in the process, optionally appending custom data.
        This also triggers a RAM sample.

        Args:
            step_data: Optional dictionary of step-specific metrics to log.
        """
        if not self.is_monitoring:
            return

        self._sample_ram()

        if self.log_file_path and self.log_file_path.exists():
            # Read, append, write back (simple approach for real-time logging)
            try:
                with open(self.log_file_path, "r") as f:
                    log_data = json.load(f)

                entry = {
                    "elapsed_seconds": time.time() - self.start_time if self.start_time else 0,
                    "ram_mb": self.ram_samples[-1] if self.ram_samples else 0,
                    "step_data": step_data
                }
                log_data["samples"].append(entry)

                # Check constraints immediately (fail loudly)
                if self.peak_ram_mb > RAM_LIMIT_MB:
                    log_data["status"] = "FAILED_RAM_LIMIT"
                    with open(self.log_file_path, "w") as f:
                        json.dump(log_data, f, indent=2)
                    raise MemoryError(f"RAM limit exceeded: {self.peak_ram_mb:.2f} MB > {RAM_LIMIT_MB} MB")

                if self.start_time and (time.time() - self.start_time) > TIME_LIMIT_SECONDS:
                    log_data["status"] = "FAILED_TIME_LIMIT"
                    with open(self.log_file_path, "w") as f:
                        json.dump(log_data, f, indent=2)
                    raise TimeoutError(f"Time limit exceeded: {time.time() - self.start_time:.2f}s > {TIME_LIMIT_SECONDS}s")

                with open(self.log_file_path, "w") as f:
                    json.dump(log_data, f, indent=2)

            except (json.JSONDecodeError, IOError) as e:
                # Fallback: append to a separate error log if main log is corrupted
                error_log_path = self.log_dir / f"error_{self.sequence_id}.log"
                with open(error_log_path, "a") as ef:
                    ef.write(f"Error updating main log: {e}\n")

    def stop(self) -> Dict[str, Any]:
        """
        Stop monitoring and return final statistics.

        Returns:
            Dictionary containing final metrics.
        """
        if not self.is_monitoring:
            raise RuntimeError("Monitor is not running.")

        self.end_time = time.time()
        self.is_monitoring = False

        # Final RAM sample
        self._sample_ram()

        total_time = self.end_time - self.start_time if self.start_time else 0

        summary = {
            "sequence_id": self.sequence_id,
            "start_time": datetime.fromtimestamp(self.start_time, tz=timezone.utc).isoformat() if self.start_time else None,
            "end_time": datetime.fromtimestamp(self.end_time, tz=timezone.utc).isoformat() if self.end_time else None,
            "wall_clock_seconds": total_time,
            "peak_ram_mb": self.peak_ram_mb,
            "status": "completed",
            "log_file": str(self.log_file_path)
        }

        # Update the main log file with final status
        if self.log_file_path and self.log_file_path.exists():
            try:
                with open(self.log_file_path, "r") as f:
                    log_data = json.load(f)
                log_data["status"] = "completed"
                log_data["summary"] = {
                    "peak_ram_mb": self.peak_ram_mb,
                    "wall_clock_seconds": total_time
                }
                with open(self.log_file_path, "w") as f:
                    json.dump(log_data, f, indent=2)
            except (json.JSONDecodeError, IOError):
                pass

        return summary

    def check_constraints(self) -> None:
        """
        Explicitly check if current resources exceed limits.
        Raises MemoryError or TimeoutError if limits are breached.
        """
        if self.start_time is None:
            return

        current_time = time.time()
        elapsed = current_time - self.start_time

        if elapsed > TIME_LIMIT_SECONDS:
            raise TimeoutError(f"Time limit exceeded: {elapsed:.2f}s > {TIME_LIMIT_SECONDS}s")

        current_ram_mb = self.process.memory_info().rss / (1024 * 1024)
        if current_ram_mb > RAM_LIMIT_MB:
            raise MemoryError(f"RAM limit exceeded: {current_ram_mb:.2f} MB > {RAM_LIMIT_MB} MB")


def log_resource_usage(sequence_id: str, step_data: Optional[Dict[str, Any]] = None, log_dir: str = "data/logs") -> ResourceMonitor:
    """
    Convenience function to start a monitor and optionally record a step.

    Args:
        sequence_id: Unique ID for the sequence.
        step_data: Optional data to log for the current step.
        log_dir: Directory for logs.

    Returns:
        The ResourceMonitor instance.
    """
    monitor = ResourceMonitor(sequence_id, log_dir)
    monitor.start()
    if step_data is not None:
        monitor.record_step(step_data)
    return monitor
