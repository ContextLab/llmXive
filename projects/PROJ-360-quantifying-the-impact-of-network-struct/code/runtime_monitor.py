"""
Runtime monitoring utilities for the llmXive pipeline.

This module provides functionality to instrument and measure the total pipeline runtime,
logging results to verify compliance with SC-005 (total runtime < 6 hours).
"""
import os
import time
import logging
import json
from pathlib import Path
from datetime import datetime
from typing import Optional

# Constants
MAX_RUNTIME_SECONDS = 6 * 3600  # 6 hours in seconds
START_TIME_FILE = Path("data/processed/pipeline_start_time.json")
RUNTIME_LOG_FILE = Path("results/runtime.log")

def setup_runtime_logger(name: str = "runtime_monitor") -> logging.Logger:
    """
    Setup and return a logger for runtime monitoring.
    
    Args:
        name: Logger name
        
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    
    if not logger.handlers:
        # Create file handler
        log_dir = Path("results")
        log_dir.mkdir(parents=True, exist_ok=True)
        
        file_handler = logging.FileHandler(log_dir / "runtime_monitor.log")
        file_handler.setLevel(logging.INFO)
        
        # Create formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(formatter)
        
        logger.addHandler(file_handler)
        
    return logger

def record_start_time(logger: Optional[logging.Logger] = None) -> float:
    """
    Record the pipeline start time to a file.
    
    Args:
        logger: Optional logger instance
        
    Returns:
        The recorded start time (Unix timestamp)
    """
    start_time = time.time()
    start_data = {
        "start_timestamp": start_time,
        "start_datetime": datetime.fromtimestamp(start_time).isoformat()
    }
    
    # Ensure data directory exists
    START_TIME_FILE.parent.mkdir(parents=True, exist_ok=True)
    
    with open(START_TIME_FILE, 'w') as f:
        json.dump(start_data, f, indent=2)
        
    if logger:
        logger.info(f"Pipeline start time recorded: {start_data['start_datetime']}")
        
    return start_time

def load_pipeline_start_time(logger: Optional[logging.Logger] = None) -> Optional[float]:
    """
    Load the pipeline start time from the stored file.
    
    Args:
        logger: Optional logger instance
        
    Returns:
        Start time (Unix timestamp) or None if not found
    """
    if not START_TIME_FILE.exists():
        if logger:
            logger.warning("Pipeline start time file not found. Cannot measure runtime.")
        return None
        
    try:
        with open(START_TIME_FILE, 'r') as f:
            data = json.load(f)
        start_time = data.get("start_timestamp")
        if logger:
            logger.info(f"Loaded pipeline start time: {datetime.fromtimestamp(start_time).isoformat()}")
        return start_time
    except (json.JSONDecodeError, KeyError) as e:
        if logger:
            logger.error(f"Error loading start time: {e}")
        return None

def measure_and_log_runtime(logger: Optional[logging.Logger] = None) -> bool:
    """
    Measure the total pipeline runtime and log the result.
    
    Reads the start time from the stored file, calculates elapsed time,
    logs the result to results/runtime.log, and asserts runtime < 6 hours.
    
    Args:
        logger: Optional logger instance
        
    Returns:
        True if runtime < 6 hours, False otherwise
    """
    if logger is None:
        logger = setup_runtime_logger()
        
    start_time = load_pipeline_start_time(logger)
    if start_time is None:
        logger.error("Cannot measure runtime: start time not recorded.")
        return False
        
    end_time = time.time()
    elapsed_seconds = end_time - start_time
    elapsed_hours = elapsed_seconds / 3600
    
    # Format duration
    hours = int(elapsed_seconds // 3600)
    minutes = int((elapsed_seconds % 3600) // 60)
    seconds = elapsed_seconds % 60
    duration_str = f"{hours}h {minutes}m {seconds:.2f}s"
    
    # Create log entry
    log_entry = {
        "start_time": datetime.fromtimestamp(start_time).isoformat(),
        "end_time": datetime.fromtimestamp(end_time).isoformat(),
        "elapsed_seconds": elapsed_seconds,
        "elapsed_hours": elapsed_hours,
        "duration_formatted": duration_str,
        "compliance_status": "PASS" if elapsed_seconds < MAX_RUNTIME_SECONDS else "FAIL",
        "max_allowed_seconds": MAX_RUNTIME_SECONDS,
        "max_allowed_hours": 6
    }
    
    # Ensure results directory exists
    RUNTIME_LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    
    # Append to runtime log
    with open(RUNTIME_LOG_FILE, 'a') as f:
        f.write(f"=== Pipeline Runtime Check ===\n")
        f.write(f"Start: {log_entry['start_time']}\n")
        f.write(f"End:   {log_entry['end_time']}\n")
        f.write(f"Elapsed: {duration_str} ({elapsed_seconds:.2f} seconds)\n")
        f.write(f"Max Allowed: 6 hours ({MAX_RUNTIME_SECONDS} seconds)\n")
        f.write(f"Status: {log_entry['compliance_status']}\n")
        f.write(f"JSON: {json.dumps(log_entry, indent=2)}\n")
        f.write(f"\n")
        
    logger.info(f"Pipeline runtime: {duration_str} ({elapsed_seconds:.2f}s)")
    logger.info(f"Compliance with SC-005 (< 6 hours): {log_entry['compliance_status']}")
    
    if elapsed_seconds >= MAX_RUNTIME_SECONDS:
        logger.error(f"Runtime violation: {elapsed_seconds:.2f}s >= {MAX_RUNTIME_SECONDS}s")
        return False
        
    return True

def main():
    """
    Main entry point for runtime monitoring.
    
    This function measures the total pipeline runtime from the recorded start time,
    logs the result to results/runtime.log, and asserts compliance with SC-005.
    """
    logger = setup_runtime_logger()
    logger.info("Starting runtime measurement for pipeline compliance check (SC-005)")
    
    success = measure_and_log_runtime(logger)
    
    if success:
        logger.info("SUCCESS: Pipeline runtime is within the 6-hour limit.")
    else:
        logger.error("FAILURE: Pipeline runtime exceeded the 6-hour limit.")
        
    return 0 if success else 1

if __name__ == "__main__":
    exit(main())
