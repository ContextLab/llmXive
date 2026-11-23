"""
Module: runtime_logger

Purpose:
    Instruments and logs the end-to-end runtime of the pipeline
    to verify against CI limits.

Functions:
    - get_project_root: Returns project root.
    - RuntimeLogger: Class to manage runtime logging.
    - main: Entry point for the script.
"""
import json
import time
from pathlib import Path
from typing import Dict, Any, Optional, Union

from utils.config import get_project_root, get_path, ensure_dir

class RuntimeLogger:
    """
    Class to manage runtime logging for the pipeline.
    """
    def __init__(self, output_path: Path):
        """
        Initializes the logger.

        Args:
            output_path (Path): Path to the output JSON file.
        """
        self.output_path = output_path
        self.start_time = None
        self.end_time = None

    def start(self):
        """
        Starts the timer.
        """
        self.start_time = time.time()
        print("Runtime logging started.")

    def stop(self):
        """
        Stops the timer and calculates duration.
        """
        self.end_time = time.time()
        duration = self.end_time - self.start_time
        print(f"Runtime logging stopped. Duration: {duration:.2f}s")
        return duration

    def save(self, duration: float, limit: float = 300.0):
        """
        Saves the runtime log to a JSON file.

        Args:
            duration (float): Duration in seconds.
            limit (float): Expected limit.
        """
        ensure_dir(self.output_path.parent)
        log_data = {
            "total_runtime_seconds": duration,
            "limit_seconds": limit,
            "limit_exceeded": duration > limit
        }
        with open(self.output_path, 'w') as f:
            json.dump(log_data, f, indent=2)

def main():
    """
    Main entry point for the runtime_logger script.
    """
    project_root = get_project_root()
    output_path = project_root / "data" / "processed" / "runtime_log.json"
    logger = RuntimeLogger(output_path)
    logger.start()
    # Simulate work
    time.sleep(1)
    duration = logger.stop()
    logger.save(duration)
    print(f"Log saved to {output_path}")

if __name__ == "__main__":
    main()
