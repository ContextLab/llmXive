import os
import json
import time
import logging
from datetime import datetime

# Ensure the directory exists
LOG_DIR = "logs"
os.makedirs(LOG_DIR, exist_ok=True)
TIMING_LOG_PATH = os.path.join(LOG_DIR, "timing_report.json")

class TimingLogger:
    """
    A utility to log model training times and UQ inference durations.
    Stores results in a JSON file for budget monitoring.
    """

    def __init__(self):
        self.timings = {}
        self.start_times = {}
        self.logger = logging.getLogger(__name__)

    def start(self, stage_name: str):
        """Start timer for a specific stage."""
        self.start_times[stage_name] = time.time()
        self.logger.info(f"Starting {stage_name}...")

    def stop(self, stage_name: str):
        """Stop timer and record duration."""
        if stage_name not in self.start_times:
            raise ValueError(f"Timer for {stage_name} was not started.")
        
        end_time = time.time()
        duration_seconds = end_time - self.start_times[stage_name]
        self.timings[stage_name] = {
            "duration_seconds": duration_seconds,
            "timestamp": datetime.now().isoformat()
        }
        self.logger.info(f"Completed {stage_name} in {duration_seconds:.2f}s")

    def save_report(self):
        """Save the accumulated timings to the JSON log file."""
        report = {
            "pipeline_run_time": datetime.now().isoformat(),
            "stages": self.timings
        }
        with open(TIMING_LOG_PATH, 'w') as f:
            json.dump(report, f, indent=2)
        self.logger.info(f"Timing report saved to {TIMING_LOG_PATH}")
        return report

    def get_total_time(self) -> float:
        """Calculate total time spent in all recorded stages."""
        return sum(t["duration_seconds"] for t in self.timings.values())

# Global instance for use across the pipeline
timing_logger = TimingLogger()
