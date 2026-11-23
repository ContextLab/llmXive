"""
Demonstration script for the logging infrastructure (Task T006).

This script exercises all major logging functions to verify that:
1. The logger initializes correctly.
2. Log files are created in the correct location.
3. All logging levels and formats are working as expected.
4. The pipeline start/end lifecycle is tracked.

Usage:
    python code/run_logging_demo.py

Output:
    - Writes a log file to data/logs/pipeline_<timestamp>.log
    - Prints logs to stdout
"""
import sys
import time
from pathlib import Path

# Ensure the project root is in the path
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.logging import (
    get_pipeline_logger,
    get_log_file_path,
    log_pipeline_start,
    log_pipeline_end,
    log_error,
    log_metric,
    log_chunk_info,
    log_task_start,
    log_task_end,
    log_data_file_created
)
from utils.config import get_project_root


def main():
    """Run the logging demonstration."""
    # Initialize configuration
    log_pipeline_start(config={"mode": "demo", "version": "1.0.0"})

    # Demonstrate task logging
    log_task_start("T006-DEMO", "Demonstrating logging infrastructure")
    
    # Simulate processing steps
    logger = get_pipeline_logger()
    
    logger.info("Initializing demo sequence...")
    
    # Log metrics
    log_metric("cpu_cores", 4, "units")
    log_metric("memory_available", 7.0, "GB")
    
    # Simulate chunk processing
    time.sleep(0.1)
    log_chunk_info(1, 3, 1000, 0.5)
    log_chunk_info(2, 3, 1500, 0.7)
    log_chunk_info(3, 3, 1200, 0.6)
    
    # Log a data file creation
    demo_file = "data/processed/demo_output.csv"
    log_data_file_created(demo_file, file_size_mb=0.5, record_count=3700)
    
    # Simulate an error
    try:
        raise ValueError("Simulated error for logging demonstration")
    except Exception as e:
        log_error("T006-DEMO-ERROR", e, {"attempt": 1, "context": "demo"})
    
    # Log task completion
    log_task_end("T006-DEMO", status="COMPLETED", output_files=[demo_file])
    
    # Print log file location
    log_path = get_log_file_path()
    logger.info(f"Log file written to: {log_path}")
    
    # End pipeline
    log_pipeline_end(status="SUCCESS")
    
    print("\n--- Logging Demo Complete ---")
    print(f"Check the log file at: {log_path}")


if __name__ == "__main__":
    main()
