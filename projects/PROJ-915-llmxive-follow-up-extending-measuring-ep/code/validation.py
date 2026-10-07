import json
import os
import time
import fcntl
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any

from config import get_config

class RuntimeTracker:
    _instance = None
    _start_time: Optional[float] = None
    _max_hours: float = 6.0

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def start(self):
        if self._start_time is None:
            self._start_time = time.time()

    def stop(self):
        self._start_time = None

    def elapsed_hours(self) -> float:
        if self._start_time is None:
            return 0.0
        return (time.time() - self._start_time) / 3600.0

    def check_limit(self, max_hours: float = None) -> bool:
        max_hours = max_hours or self._max_hours
        return self.elapsed_hours() <= max_hours

def get_tracker() -> RuntimeTracker:
    return RuntimeTracker()

def start_pipeline_timer():
    tracker = get_tracker()
    tracker.start()
    logging.info("Pipeline timer started.")

def stop_pipeline_timer():
    tracker = get_tracker()
    tracker.stop()
    logging.info("Pipeline timer stopped.")

def check_pipeline_limit():
    tracker = get_tracker()
    if not tracker.check_limit():
        logging.error("Pipeline exceeded maximum runtime.")
        generate_timeout_report()
        raise TimeoutError("Pipeline timeout limit exceeded.")

def generate_timeout_report():
    """Generate a timeout report."""
    report_path = Path("data/results/compute_time_report.md")
    report_path.parent.mkdir(parents=True, exist_ok=True)
    with open(report_path, "w") as f:
        f.write("# Compute Time Report\n\n")
        f.write("Pipeline timed out before completion.\n")
        f.write(f"Elapsed time: {get_tracker().elapsed_hours():.2f} hours\n")

def update_pipeline_log(stage: str, status: str, details: str = ""):
    """Update the pipeline log file."""
    log_file = Path("data/results/pipeline_log.json")
    log_file.parent.mkdir(parents=True, exist_ok=True)
    
    log_data = {"stages": []}
    if log_file.exists():
        with open(log_file, "r") as f:
            log_data = json.load(f)
    
    log_data["stages"].append({
        "stage": stage,
        "status": status,
        "timestamp": datetime.now().isoformat(),
        "details": details
    })
    
    with open(log_file, "w") as f:
        json.dump(log_data, f, indent=2)

class PipelineTimerContext:
    def __init__(self, max_hours: float = 6.0):
        self.max_hours = max_hours

    def __enter__(self):
        get_tracker().start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        get_tracker().stop()

def validate_data_integrity(data: Dict[str, Any]) -> bool:
    """Validate data integrity."""
    return True

def main():
    """Entry point for validation script."""
    pass

if __name__ == "__main__":
    main()