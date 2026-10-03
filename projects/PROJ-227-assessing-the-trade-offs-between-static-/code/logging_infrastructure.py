"""
Logging Infrastructure for the LLM Analysis Trade-offs Pipeline.

Provides a thread-safe JSON Lines logger for resource metrics (CPU, RAM)
and a background monitor to capture these metrics at regular intervals.
"""

import json
import os
import time
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import psutil
from filelock import FileLock

# Project root relative to this file's location (code/)
PROJECT_ROOT = Path(__file__).parent.parent
LOGS_DIR = PROJECT_ROOT / "data" / "logs"
LOG_FILE = LOGS_DIR / "pipeline.log"
LOCK_FILE = LOGS_DIR / ".pipeline.log.lock"

# Default logging interval in seconds
DEFAULT_INTERVAL = 5.0


class ResourceMonitor:
    """
    Monitors system resource usage (CPU and RAM) and logs it to a JSON Lines file.

    The monitor runs in a background thread and uses file locking to ensure
    thread-safe writes to the log file.
    """

    def __init__(self, interval: float = DEFAULT_INTERVAL, log_file: Optional[Path] = None):
        self.interval = interval
        self.log_file = log_file or LOG_FILE
        self.lock_file = LOCK_FILE
        self.stop_event = threading.Event()
        self.thread: Optional[threading.Thread] = None
        self.process = psutil.Process()

    def _ensure_log_directory(self) -> None:
        """Ensures the log directory exists."""
        self.log_file.parent.mkdir(parents=True, exist_ok=True)

    def _get_resource_metrics(self) -> dict:
        """
        Collects current CPU and RAM metrics.

        Returns:
            dict: A dictionary containing timestamp, cpu_percent, ram_percent, and pid.
        """
        # cpu_percent(interval=None) returns the CPU usage since the last call.
        # We use a short interval (0.1) to get a responsive value without blocking too long.
        cpu = self.process.cpu_percent(interval=0.1)
        ram_info = self.process.memory_percent()

        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "cpu_percent": float(cpu),
            "ram_percent": float(ram_info),
            "pid": self.process.pid
        }

    def _log_metrics(self) -> None:
        """Collects metrics and writes them to the log file with locking."""
        metrics = self._get_resource_metrics()
        self._ensure_log_directory()

        # Use filelock for thread-safe writes
        with FileLock(str(self.lock_file)):
            with open(self.log_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(metrics) + "\n")

    def _run_loop(self) -> None:
        """Background loop that logs metrics at the specified interval."""
        while not self.stop_event.is_set():
            try:
                self._log_metrics()
            except Exception as e:
                # Log errors to stderr to avoid crashing the monitor thread
                # but keep the main pipeline running if possible.
                print(f"Error in ResourceMonitor: {e}", file=sys.stderr)

            # Wait for the interval, but check stop_event periodically
            # to allow for faster shutdown if needed.
            if self.stop_event.wait(timeout=self.interval):
                break

    def start(self) -> None:
        """Starts the background monitoring thread."""
        if self.thread is not None and self.thread.is_alive():
            return  # Already running

        self.stop_event.clear()
        self.thread = threading.Thread(target=self._run_loop, daemon=True)
        self.thread.start()

    def stop(self) -> None:
        """Stops the background monitoring thread."""
        if self.thread is None or not self.thread.is_alive():
            return

        self.stop_event.set()
        self.thread.join(timeout=self.interval + 1.0)


def setup_pipeline_logging(interval: float = DEFAULT_INTERVAL) -> ResourceMonitor:
    """
    Sets up the pipeline logging infrastructure.

    Args:
        interval: The interval in seconds between resource metric logs.

    Returns:
        ResourceMonitor: The started monitor instance.
    """
    monitor = ResourceMonitor(interval=interval)
    monitor.start()
    return monitor


def main():
    """
    Main entry point for testing the logging infrastructure.

    Runs a monitor for a short duration, stops it, and verifies the log file.
    """
    import sys

    print("Starting Resource Monitor...")
    monitor = setup_pipeline_logging(interval=2.0)

    # Run for 10 seconds to generate some logs
    time.sleep(10)

    print("Stopping Resource Monitor...")
    monitor.stop()

    # Verify the log file
    if LOG_FILE.exists():
        print(f"Log file created at: {LOG_FILE}")
        with open(LOG_FILE, "r", encoding="utf-8") as f:
            lines = f.readlines()
            print(f"Number of log entries: {len(lines)}")
            
            # Validate schema of first entry
            if lines:
                try:
                    entry = json.loads(lines[0])
                    required_keys = {"timestamp", "cpu_percent", "ram_percent", "pid"}
                    if required_keys.issubset(entry.keys()):
                        print("Schema validation: PASSED")
                        print(f"Sample entry: {entry}")
                    else:
                        print("Schema validation: FAILED - Missing keys")
                except json.JSONDecodeError:
                    print("Schema validation: FAILED - Invalid JSON")
    else:
        print("ERROR: Log file was not created.")
        sys.exit(1)

    print("Logging infrastructure test completed successfully.")


if __name__ == "__main__":
    main()
