"""
Runtime logging module for the EEG analysis pipeline.

Implements logic to track pipeline execution time and generate
the runtime log artifact required for SC-002 verification.
"""
import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path

# Import shared config for paths
from config import ensure_directories

# Project root relative to this file
PROJECT_ROOT = Path(__file__).resolve().parent.parent
METRICS_DIR = PROJECT_ROOT / "data" / "metrics"
LOGS_DIR = PROJECT_ROOT / "logs"
LOG_FILE = LOGS_DIR / "processing.log"
RUNTIME_LOG_FILE = METRICS_DIR / "runtime_log.json"

# Global timer start
_start_time: float | None = None
_start_datetime: datetime | None = None

def ensure_metrics_directory():
    """Ensure the metrics directory exists."""
    ensure_directories()
    METRICS_DIR.mkdir(parents=True, exist_ok=True)
    LOGS_DIR.mkdir(parents=True, exist_ok=True)

def start_timer():
    """Start the global pipeline timer."""
    global _start_time, _start_datetime
    _start_time = time.time()
    _start_datetime = datetime.now()
    logging_setup = __import__('logging_setup', fromlist=['get_logger'])
    logger = logging_setup.get_logger()
    logger.info(f"Pipeline started at {_start_datetime.isoformat()}")

def get_elapsed_minutes():
    """Calculate elapsed time in minutes since start_timer was called."""
    if _start_time is None:
        raise RuntimeError("Timer not started. Call start_timer() first.")
    return (time.time() - _start_time) / 60.0

def save_runtime_log(status: str = "success"):
    """
    Generate and save the runtime_log.json artifact.
    
    Args:
        status: 'success' or 'timeout'
    """
    if _start_time is None:
        raise RuntimeError("Timer not started. Cannot save runtime log.")
    
    ensure_metrics_directory()
    
    end_datetime = datetime.now()
    total_duration_minutes = get_elapsed_minutes()
    
    log_entry = {
        "start_time": _start_datetime.isoformat(),
        "end_time": end_datetime.isoformat(),
        "total_duration_minutes": round(total_duration_minutes, 4),
        "status": status
    }
    
    # Write to JSON file
    with open(RUNTIME_LOG_FILE, 'w') as f:
        json.dump(log_entry, f, indent=2)
    
    # Log to processing.log as well
    logging_setup = __import__('logging_setup', fromlist=['get_logger'])
    logger = logging_setup.get_logger()
    logger.info(f"Pipeline finished. Status: {status}, Duration: {total_duration_minutes:.2f} minutes")
    
    print(f"Runtime log saved to {RUNTIME_LOG_FILE}")
    return log_entry

def main():
    """
    CLI entry point for testing the runtime logger.
    Simulates a pipeline run and generates the log.
    """
    import logging
    from logging_setup import initialize_logging_and_tracking
    
    # Initialize logging
    initialize_logging_and_tracking()
    
    print("Starting runtime logger test...")
    start_timer()
    
    # Simulate some work
    time.sleep(1)
    
    # Save the log
    result = save_runtime_log(status="success")
    print(f"Result: {result}")

if __name__ == "__main__":
    main()