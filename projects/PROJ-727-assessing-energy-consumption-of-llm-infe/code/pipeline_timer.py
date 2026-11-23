"""
Pipeline Timer Module for T034 Verification.

This module handles the timing of the full pipeline execution and logs
the duration to `logs/pipeline_duration.log`.
"""
import os
import sys
import time
import logging
from datetime import datetime
from pathlib import Path
from code.config import DATA_PROCESSED_DIR, LOGS_DIR

def setup_logging():
    """Ensures the logs directory exists and configures a file handler."""
    os.makedirs(LOGS_DIR, exist_ok=True)
    log_file = os.path.join(LOGS_DIR, "pipeline_duration.log")
    
    # Create a logger specific to timing
    logger = logging.getLogger("pipeline_timer")
    logger.setLevel(logging.INFO)
    
    # Clear existing handlers to avoid duplicates if called multiple times
    if logger.handlers:
        logger.handlers.clear()
    
    # File handler for duration logs
    fh = logging.FileHandler(log_file, mode='w')
    fh.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(message)s')
    fh.setFormatter(formatter)
    logger.addHandler(fh)
    
    # Also log to console for immediate feedback
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    ch.setFormatter(formatter)
    logger.addHandler(ch)
    
    return logger

def run_full_pipeline():
    """
    Executes the full pipeline and measures the total time.
    Calls the main orchestrator in code.main.
    """
    logger = setup_logging()
    logger.info(f"Pipeline start time: {datetime.now().isoformat()}")
    
    start_time = time.time()
    
    try:
        from code.main import run_full_pipeline as orchestrator
        orchestrator()
    except Exception as e:
        end_time = time.time()
        duration = end_time - start_time
        logger.error(f"Pipeline failed after {duration:.2f} seconds: {e}")
        raise

    end_time = time.time()
    duration = end_time - start_time
    
    logger.info(f"Pipeline end time: {datetime.now().isoformat()}")
    logger.info(f"Total execution time: {duration:.2f} seconds")
    logger.info(f"Total execution time: {duration/3600:.4f} hours")
    
    # Verify constraint (6 hours = 21600 seconds)
    if duration > 21600:
        logger.warning(f"WARNING: Pipeline exceeded 6-hour limit ({duration:.2f}s > 21600s)")
    else:
        logger.info(f"SUCCESS: Pipeline completed within 6-hour limit ({duration:.2f}s < 21600s)")
    
    return duration

def main():
    """Entry point for the timer script."""
    duration = run_full_pipeline()
    print(f"Total pipeline duration: {duration:.2f} seconds")

if __name__ == "__main__":
    main()
