import os
import json
import time
import logging
from datetime import datetime
from pathlib import Path

class TimingLogger:
    def __init__(self, log_file: str = "logs/timing.log"):
        self.log_file = Path(log_file)
        self.log_file.parent.mkdir(parents=True, exist_ok=True)
        self.start_times = {}
        self.metrics = {}

    def start(self, key: str):
        self.start_times[key] = time.time()

    def stop(self, key: str):
        if key in self.start_times:
            elapsed = time.time() - self.start_times[key]
            self.metrics[key] = elapsed
            with open(self.log_file, 'a') as f:
                f.write(f"{datetime.now()}: {key} took {elapsed:.2f}s\n")

    def save_metrics(self, output_path: str):
        with open(output_path, 'w') as f:
            json.dump(self.metrics, f, indent=2)
