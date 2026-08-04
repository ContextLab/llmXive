"""
Runtime logging module for tracking pipeline execution time and status.
"""
import os
import json
import time
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

# Global variables for timing
_start_time: Optional[float] = None
_start_datetime: Optional[datetime] = None
_end_time: Optional[float] = None
_end_datetime: Optional[datetime] = None
_status: str = "running"

def start_timer():
    """Start the runtime timer."""
    global _start_time, _start_datetime, _status
    _start_time = time.time()
    _start_datetime = datetime.now()
    _status = "running"
    logger.info(f"Timer started at {_start_datetime.isoformat()}")

def end_timer(status: str = "success"):
    """
    Stop the runtime timer and record the end time.
    
    Args:
        status: Status of the pipeline ('success' or 'failed')
    """
    global _end_time, _end_datetime, _status
    _end_time = time.time()
    _end_datetime = datetime.now()
    _status = status
    duration = get_elapsed_seconds()
    logger.info(f"Timer ended at {_end_datetime.isoformat()}. Duration: {duration:.2f} seconds")

def get_elapsed_seconds() -> float:
    """
    Get the elapsed time in seconds.
    
    Returns:
        Elapsed time in seconds, or 0 if timer hasn't started
    """
    if _start_time is None:
        return 0.0
    
    end = _end_time if _end_time is not None else time.time()
    return end - _start_time

def persist_runtime_log(output_path: str = "data/benchmarks/runtime_log.json"):
    """
    Persist the runtime log to a JSON file.
    
    Args:
        output_path: Path to the output JSON file
    """
    global _start_datetime, _end_datetime, _status
    
    # Ensure output directory exists
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    # Prepare log data
    log_data = {
        "start_time": _start_datetime.isoformat() if _start_datetime else None,
        "end_time": _end_datetime.isoformat() if _end_datetime else None,
        "duration_seconds": get_elapsed_seconds(),
        "status": _status
    }
    
    # Write to file
    with open(output_file, 'w') as f:
        json.dump(log_data, f, indent=2)
    
    logger.info(f"Runtime log saved to {output_file}")
    
    # Verify the 4-hour threshold (SC-004)
    duration_hours = get_elapsed_seconds() / 3600
    if duration_hours > 4:
        logger.warning(f"Pipeline duration ({duration_hours:.2f} hours) exceeds 4-hour threshold (SC-004)")
    else:
        logger.info(f"Pipeline duration ({duration_hours:.2f} hours) is within 4-hour threshold (SC-004)")
    
    return log_data

def main():
    """Main function for testing runtime logger."""
    logging.basicConfig(level=logging.INFO)
    
    # Example usage
    start_timer()
    time.sleep(1)  # Simulate work
    end_timer("success")
    
    log_data = persist_runtime_log()
    print(json.dumps(log_data, indent=2))

if __name__ == "__main__":
    main()
