"""
Module to check pipeline runtime against the SC-004 threshold.
Parses logs/pipeline.log for start and end timestamps.
"""
import os
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional, Tuple

from code.config import get_output_path
from code.utils.logging import get_logger

# Constants
RUNTIME_THRESHOLD_HOURS = 4.0
LOG_FILE_NAME = "pipeline.log"
OUTPUT_FILE_NAME = "metrics.json"
START_MARKER = "Starting data ingestion"  # T012 start
END_MARKER_US1 = "Pipeline execution completed (US1)"
END_MARKER_US4 = "Pipeline execution completed (US4)"

logger = get_logger(__name__)

def parse_log_timestamps(log_path: Path) -> Tuple[Optional[datetime], Optional[datetime]]:
    """
    Parse the log file to find the start and end timestamps.
    
    Args:
        log_path: Path to the log file.
        
    Returns:
        Tuple of (start_time, end_time). If not found, returns None.
    """
    if not log_path.exists():
        logger.error(f"Log file not found: {log_path}")
        return None, None

    start_time = None
    end_time = None

    try:
        with open(log_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
    except Exception as e:
        logger.error(f"Failed to read log file: {e}")
        return None, None

    # Format assumption: "YYYY-MM-DD HH:MM:SS,mmm - LEVEL - Message"
    # We look for the specific markers and parse the timestamp from the line.
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
        
        # Try to extract timestamp from the beginning of the line
        # Expected format: 2023-10-27 10:00:00,123 - INFO - ...
        # We look for the first 23 characters (YYYY-MM-DD HH:MM:SS,mmm)
        if len(line) < 23:
            continue

        try:
            # Extract timestamp string
            ts_str = line[:23]
            # Parse it. The format is YYYY-MM-DD HH:MM:SS,mmm
            # datetime.strptime doesn't handle milliseconds well by default, so we split
            if ',' in ts_str:
                date_part, ms_part = ts_str.split(',')
                dt = datetime.strptime(date_part, "%Y-%m-%d %H:%M:%S")
                # We ignore milliseconds for duration calculation as they are negligible for hours
            else:
                dt = datetime.strptime(ts_str, "%Y-%m-%d %H:%M:%S")

            if START_MARKER in line and start_time is None:
                start_time = dt
                logger.info(f"Found start timestamp: {start_time}")
            
            # Check for end markers. We want the LAST occurrence if multiple exist,
            # or the first one if we only expect one. The spec says "end of T030 OR end of T032a".
            # We'll take the latest timestamp found for any end marker.
            if (END_MARKER_US1 in line or END_MARKER_US4 in line):
                end_time = dt
                logger.info(f"Found end timestamp: {end_time}")
                
        except ValueError as e:
            # Skip lines that don't match the expected timestamp format
            continue

    return start_time, end_time

def calculate_runtime_hours(start_time: Optional[datetime], end_time: Optional[datetime]) -> Optional[float]:
    """
    Calculate the runtime in hours.
    
    Args:
        start_time: Start datetime.
        end_time: End datetime.
        
    Returns:
        Runtime in hours, or None if times are missing.
    """
    if start_time is None or end_time is None:
        logger.warning("Start or end time is missing. Cannot calculate runtime.")
        return None

    delta = end_time - start_time
    total_seconds = delta.total_seconds()
    hours = total_seconds / 3600.0
    return hours

def run_runtime_check() -> dict:
    """
    Execute the runtime check logic.
    
    Returns:
        Dictionary with runtime metrics.
    """
    log_path = Path("logs") / LOG_FILE_NAME
    
    logger.info(f"Checking runtime from log file: {log_path}")
    
    start_time, end_time = parse_log_timestamps(log_path)
    runtime_hours = calculate_runtime_hours(start_time, end_time)
    
    result = {
        "start_time": start_time.isoformat() if start_time else None,
        "end_time": end_time.isoformat() if end_time else None,
        "total_runtime_hours": runtime_hours,
        "threshold_hours": RUNTIME_THRESHOLD_HOURS,
        "passed": False
    }
    
    if runtime_hours is not None:
        result["passed"] = runtime_hours <= RUNTIME_THRESHOLD_HOURS
        status = "PASS" if result["passed"] else "FAIL"
        logger.info(f"Runtime check: {status}. Runtime: {runtime_hours:.2f} hours. Threshold: {RUNTIME_THRESHOLD_HOURS} hours.")
    else:
        logger.error("Runtime check FAILED: Could not determine runtime.")
        result["passed"] = False
        
    return result

def main():
    """
    Main entry point for the runtime check script.
    Writes results to results/metrics.json.
    """
    logger.info("Starting runtime check (T037)...")
    
    results = run_runtime_check()
    
    # Ensure output directory exists
    output_dir = Path("results")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    output_path = output_dir / OUTPUT_FILE_NAME
    
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2)
        logger.info(f"Runtime metrics written to {output_path}")
    except Exception as e:
        logger.error(f"Failed to write metrics file: {e}")
        raise

    logger.info("Runtime check completed.")
    return results

if __name__ == "__main__":
    main()
