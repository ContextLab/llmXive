"""
Utility module for logging runtime metrics.
Ensures execution time is explicitly logged for SC-005.
"""

import logging
import time
from pathlib import Path

logger = logging.getLogger(__name__)

def log_duration(start_time: float, end_time: float, log_file: Path):
    """
    Calculates duration and logs it to stdout and a file.
    
    Args:
        start_time: Start timestamp (time.time())
        end_time: End timestamp (time.time())
        log_file: Path to the log file.
    """
    duration = end_time - start_time
    
    # Ensure log directory exists
    log_file.parent.mkdir(parents=True, exist_ok=True)
    
    # Configure file handler if not already present
    file_handler = None
    for handler in logger.handlers:
        if isinstance(handler, logging.FileHandler) and handler.baseFilename == str(log_file):
            file_handler = handler
            break
    
    if not file_handler:
        file_handler = logging.FileHandler(log_file, mode='w')
        file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
        logger.addHandler(file_handler)
    
    logger.info(f"Total Execution Duration: {duration:.6f} seconds")
    logger.info(f"SC-005_MEASURED_DURATION_SECONDS: {duration:.6f}")
    
    return duration
