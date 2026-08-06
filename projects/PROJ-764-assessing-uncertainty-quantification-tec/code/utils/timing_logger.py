import os
import json
import time
import logging
from datetime import datetime
from pathlib import Path

class TimingLogger:
    def __init__(self, logger: logging.Logger = None):
        self.logger = logger or logging.getLogger(__name__)
        self.timings = {}
        self.start_times = {}
    
    def start(self, task_name: str):
        self.start_times[task_name] = time.time()
        self.logger.info(f"Starting task: {task_name}")
    
    def end(self, task_name: str):
        if task_name in self.start_times:
            duration = time.time() - self.start_times[task_name]
            self.timings[task_name] = duration
            self.logger.info(f"Completed task: {task_name} in {duration:.2f}s")
            del self.start_times[task_name]
        else:
            self.logger.warning(f"Task {task_name} ended without being started.")
    
    def finish(self):
        remaining = list(self.start_times.keys())
        if remaining:
            self.logger.warning(f"Tasks not completed: {remaining}")
    
    def save(self, output_path: str = "results/timing_report.json"):
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        report = {
            "start_time": datetime.now().isoformat(),
            "timings": self.timings,
            "total_duration": sum(self.timings.values())
        }
        with open(output_path, 'w') as f:
            json.dump(report, f, indent=2)
        self.logger.info(f"Timing report saved to {output_path}")