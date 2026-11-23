import os
import csv
import json
import time
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime

from config import get_path, load_config

logger = logging.getLogger(__name__)

def get_current_timestamp() -> float:
    """Return the current wall-clock time in seconds."""
    return time.time()

def format_duration(seconds: float) -> str:
    """Convert seconds to a human-readable string (HH:MM:SS.ms)."""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = seconds % 60
    return f"{hours:02d}:{minutes:02d}:{secs:06.3f}"

def record_execution_time(start_time: float, end_time: float, config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Calculate execution metrics and format them for the results record.
    
    Args:
        start_time: Timestamp in seconds when the pipeline started.
        end_time: Timestamp in seconds when the pipeline ended.
        config: The loaded configuration dictionary.
    
    Returns:
        A dictionary containing timing metrics.
    """
    total_seconds = end_time - start_time
    
    return {
        "start_timestamp": datetime.fromtimestamp(start_time).isoformat(),
        "end_timestamp": datetime.fromtimestamp(end_time).isoformat(),
        "total_execution_time_seconds": round(total_seconds, 3),
        "total_execution_time_formatted": format_duration(total_seconds),
        "pipeline_version": config.get("pipeline", {}).get("version", "unknown"),
        "timestamp_recorded": datetime.now().isoformat()
    }

def write_timing_to_results(
    timing_data: Dict[str, Any], 
    results_path: Path,
    additional_metrics: Optional[Dict[str, Any]] = None
) -> None:
    """
    Append timing data to the reconstruction_results.csv file.
    If the file does not exist, create it with headers.
    
    Args:
        timing_data: Dictionary containing timing metrics.
        results_path: Path to the results CSV file.
        additional_metrics: Optional dictionary of other metrics to include in the row.
    """
    fieldnames = [
        "metric_name", 
        "metric_value", 
        "unit", 
        "timestamp", 
        "details"
    ]
    
    # Prepare the row data
    row_data = {
        "metric_name": "SC-005_total_execution_time",
        "metric_value": timing_data["total_execution_time_seconds"],
        "unit": "seconds",
        "timestamp": timing_data["timestamp_recorded"],
        "details": json.dumps(timing_data)
    }
    
    # Merge with additional metrics if provided
    if additional_metrics:
        for key, value in additional_metrics.items():
            if key not in row_data:
                row_data[key] = value
    
    # Ensure the directory exists
    results_path.parent.mkdir(parents=True, exist_ok=True)
    
    file_exists = results_path.exists()
    
    with open(results_path, mode='a', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        
        if not file_exists:
            writer.writeheader()
        
        writer.writerow(row_data)
    
    logger.info(f"Execution time recorded: {timing_data['total_execution_time_formatted']} to {results_path}")

def main():
    """
    Standalone entry point to demonstrate timing instrumentation.
    In a real pipeline, this would be called after the main processing loop.
    """
    config = load_config()
    start = get_current_timestamp()
    
    # Simulate a heavy processing step (e.g., running the solver or metrics)
    logger.info("Simulating pipeline execution...")
    time.sleep(0.5) 
    end = get_current_timestamp()
    
    timing_data = record_execution_time(start, end, config)
    
    results_path = get_path("reconstruction_results_csv")
    write_timing_to_results(timing_data, results_path)
    
    print(f"Timing recorded: {timing_data['total_execution_time_formatted']}")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
