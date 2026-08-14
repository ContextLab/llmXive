"""
Logging utilities for the llmXive research pipeline.

This module provides a context manager and helper functions to track
execution time and resource usage for scripts invoked by the run-book.
It is designed to be used as a wrapper around other commands (e.g.,
stats_runner.py) to ensure resource constraints are met.
"""

import os
import sys
import time
import json
import argparse
import logging
import subprocess
from datetime import datetime
from typing import Optional, Dict, Any

# Import the active monitor from the existing utils module
from code.utils.monitor import ActiveMonitor

# Configure logging for this module
logger = logging.getLogger(__name__)


class ExecutionTracker:
    """
    Tracks the execution of a subprocess command, logging start/end times,
    exit codes, and resource usage (via ActiveMonitor).
    """

    def __init__(self, command: list[str], track_id: str = "default"):
        self.command = command
        self.track_id = track_id
        self.start_time: Optional[float] = None
        self.end_time: Optional[float] = None
        self.exit_code: int = -1
        self.monitor = ActiveMonitor()
        self.log_path = "data/processed/execution_logs.json"

    def _ensure_log_dir(self):
        """Ensure the directory for execution logs exists."""
        log_dir = os.path.dirname(self.log_path)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir, exist_ok=True)

    def _load_existing_logs(self) -> Dict[str, Any]:
        """Load existing execution logs if the file exists."""
        if os.path.exists(self.log_path):
            try:
                with open(self.log_path, 'r') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                return {}
        return {}

    def _save_logs(self, logs: Dict[str, Any]):
        """Save the updated logs to disk."""
        self._ensure_log_dir()
        with open(self.log_path, 'w') as f:
            json.dump(logs, f, indent=2)

    def run(self) -> int:
        """
        Execute the command, monitor resources, and log results.
        Returns the exit code of the subprocess.
        """
        logger.info(f"Starting execution tracking for command: {' '.join(self.command)}")
        self._ensure_log_dir()

        # Start monitoring
        self.monitor.start()
        self.start_time = time.time()

        try:
            # Run the command
            result = subprocess.run(
                self.command,
                check=False,
                capture_output=True,
                text=True
            )
            self.exit_code = result.returncode

            # Log stdout/stderr if present
            if result.stdout:
                logger.info(f"Command stdout:\n{result.stdout}")
            if result.stderr:
                logger.warning(f"Command stderr:\n{result.stderr}")

        except Exception as e:
            logger.error(f"Exception during command execution: {e}")
            self.exit_code = 1
        finally:
            # Stop monitoring
            self.monitor.stop()
            self.end_time = time.time()

            # Calculate metrics
            duration = self.end_time - self.start_time
            peak_memory = self.monitor.get_peak_memory_mb()

            # Prepare log entry
            entry = {
                "track_id": self.track_id,
                "command": " ".join(self.command),
                "start_time": datetime.fromtimestamp(self.start_time).isoformat(),
                "end_time": datetime.fromtimestamp(self.end_time).isoformat(),
                "duration_seconds": duration,
                "exit_code": self.exit_code,
                "peak_memory_mb": peak_memory
            }

            # Save to persistent log
            logs = self._load_existing_logs()
            logs[self.track_id] = entry
            self._save_logs(logs)

            logger.info(f"Execution completed. Exit code: {self.exit_code}, Duration: {duration:.2f}s, Peak Memory: {peak_memory:.2f}MB")

        return self.exit_code


def main():
    """
    Entry point for code/utils/logging.py.
    Usage: python code/utils/logging.py --track <id> --command "python <script.py> ..."
    """
    parser = argparse.ArgumentParser(description="Track execution of a command")
    parser.add_argument("--track", type=str, required=True, help="Unique ID for this execution track")
    parser.add_argument("--command", type=str, required=True, help="The command to execute (wrapped in quotes)")

    args = parser.parse_args()

    # Parse the command string into a list
    # Simple split; for complex shells, subprocess might need shell=True,
    # but for safety and consistency with other scripts, we split by space.
    # If the command contains arguments with spaces, the user should quote them properly.
    cmd_list = args.command.split()

    tracker = ExecutionTracker(cmd_list, args.track)
    exit_code = tracker.run()

    sys.exit(exit_code)


if __name__ == "__main__":
    main()