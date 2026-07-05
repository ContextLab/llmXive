"""
Runtime monitoring script for the thermal conductivity pipeline.

This script instruments the total pipeline runtime by measuring the elapsed time
from the start of the first major task (download) to the completion of the final
task (report generation). It logs the elapsed time to `results/runtime.log` and
asserts that the total time is less than 6 hours (21600 seconds) to verify
compliance with SC-005.

Usage:
    python code/runtime_monitor.py
"""
import os
import time
import logging
import json
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any

# Import existing utilities to ensure consistent logging setup
from utils import setup_logging

# Define paths relative to project root
PROJECT_ROOT = Path(__file__).resolve().parent.parent
RESULTS_DIR = PROJECT_ROOT / "results"
RUNTIME_LOG_PATH = RESULTS_DIR / "runtime.log"

# SC-005 Constraint: Pipeline must complete within 6 hours
MAX_RUNTIME_SECONDS = 6 * 60 * 60  # 21600 seconds

def setup_runtime_logger() -> logging.Logger:
    """
    Setup a dedicated logger for runtime monitoring.
    
    Returns:
        Logger configured to write to results/runtime.log.
    """
    logger = logging.getLogger("runtime_monitor")
    logger.setLevel(logging.INFO)
    
    # Clear existing handlers to avoid duplicates if called multiple times
    if logger.handlers:
        logger.handlers.clear()
    
    # Ensure results directory exists
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    
    # File handler for runtime.log
    file_handler = logging.FileHandler(RUNTIME_LOG_PATH, mode='w')
    file_handler.setLevel(logging.INFO)
    
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    # Also log to console for immediate feedback
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    return logger

def load_pipeline_start_time() -> Optional[float]:
    """
    Attempt to load a start timestamp from a marker file if it exists.
    This allows the monitor to be run separately after the pipeline,
    assuming the pipeline writes a start marker.
    
    If no marker exists, returns None.
    """
    marker_path = RESULTS_DIR / ".pipeline_start_marker"
    if marker_path.exists():
        try:
            with open(marker_path, 'r') as f:
                data = json.load(f)
                return float(data.get('start_time'))
        except (json.JSONDecodeError, ValueError, KeyError):
            return None
    return None

def record_start_time() -> float:
    """
    Record the current time as the pipeline start time.
    Returns the timestamp.
    """
    start_time = time.time()
    marker_path = RESULTS_DIR / ".pipeline_start_marker"
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    
    with open(marker_path, 'w') as f:
        json.dump({'start_time': start_time}, f)
    
    return start_time

def measure_and_log_runtime(logger: logging.Logger, start_time: Optional[float] = None) -> Dict[str, Any]:
    """
    Measure the elapsed time, log it, and assert compliance with SC-005.
    
    Args:
        logger: The runtime logger.
        start_time: Optional start timestamp. If None, attempts to load from marker.
        
    Returns:
        A dictionary containing the runtime metrics.
    """
    end_time = time.time()
    
    # Determine start time
    if start_time is None:
        start_time = load_pipeline_start_time()
    
    if start_time is None:
        logger.error("Could not determine pipeline start time. "
                     "Ensure the pipeline writes a start marker or run this script "
                     "immediately after starting the pipeline.")
        return {"error": "missing_start_time"}
    
    elapsed_seconds = end_time - start_time
    elapsed_hours = elapsed_seconds / 3600.0
    
    # Log the result
    logger.info("=" * 50)
    logger.info("PIPELINE RUNTIME MEASUREMENT")
    logger.info("=" * 50)
    logger.info(f"Start Time: {datetime.fromtimestamp(start_time).isoformat()}")
    logger.info(f"End Time:   {datetime.fromtimestamp(end_time).isoformat()}")
    logger.info(f"Elapsed Time: {elapsed_seconds:.2f} seconds ({elapsed_hours:.2f} hours)")
    
    # Compliance Check (SC-005)
    is_compliant = elapsed_seconds < MAX_RUNTIME_SECONDS
    status = "COMPLIANT" if is_compliant else "NON-COMPLIANT"
    
    logger.info(f"SC-005 Limit: {MAX_RUNTIME_SECONDS} seconds (6 hours)")
    logger.info(f"Status: {status}")
    
    if not is_compliant:
        logger.warning("WARNING: Pipeline execution exceeded the 6-hour limit defined in SC-005.")
        logger.warning("Optimization or resource scaling may be required.")
    else:
        logger.info("SUCCESS: Pipeline completed within the required 6-hour window.")
    
    logger.info("=" * 50)
    
    # Save a summary JSON for programmatic access
    summary = {
        "start_time": start_time,
        "end_time": end_time,
        "elapsed_seconds": elapsed_seconds,
        "elapsed_hours": elapsed_hours,
        "limit_seconds": MAX_RUNTIME_SECONDS,
        "compliant": is_compliant,
        "status": status
    }
    
    summary_path = RESULTS_DIR / "runtime_summary.json"
    with open(summary_path, 'w') as f:
        json.dump(summary, f, indent=2)
    
    logger.info(f"Summary saved to: {summary_path}")
    
    return summary

def main():
    """
    Entry point for the runtime monitor.
    
    If run as a standalone script, it measures the time since the pipeline
    start marker was created.
    
    If the pipeline has not been started (no marker), it will create a marker
    and wait for the user to signal completion (or just measure from now if
    intended to be run at the end).
    """
    logger = setup_runtime_logger()
    logger.info("Starting Runtime Monitor...")
    
    # Check if marker exists
    marker_path = RESULTS_DIR / ".pipeline_start_marker"
    
    if not marker_path.exists():
        logger.warning("No pipeline start marker found.")
        choice = input("Pipeline not started. Do you want to start the timer now? (y/n): ")
        if choice.lower() == 'y':
            record_start_time()
            logger.info("Timer started. Please run the pipeline and then run this script again to measure.")
            return
        else:
            logger.error("Aborted. No start time available.")
            return
    
    # Measure and log
    summary = measure_and_log_runtime(logger)
    
    if "error" in summary:
        logger.error("Runtime measurement failed.")
        return 1
    
    if not summary.get("compliant", False):
        logger.error("Pipeline did not meet SC-005 requirements.")
        return 1
    
    logger.info("Runtime monitoring completed successfully.")
    return 0

if __name__ == "__main__":
    exit(main())
