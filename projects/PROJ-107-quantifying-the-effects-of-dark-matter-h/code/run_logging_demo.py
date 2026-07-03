"""
Demonstration script for the logging infrastructure.
This script exercises all logging utilities and writes a real log file
to data/outputs/logs/ to verify the implementation works end-to-end.
"""
import sys
import time
from pathlib import Path

# Ensure code/ is in path
sys.path.insert(0, str(Path(__file__).parent))

from utils.logging import (
    get_pipeline_logger,
    log_pipeline_start,
    log_pipeline_end,
    log_error,
    log_metric,
    get_log_file_path
)

def main():
    """Run a demonstration of the logging pipeline."""
    print("Starting Logging Infrastructure Demo...")
    
    # Initialize logger
    logger = get_pipeline_logger(
        name="llmXive_Demo",
        level="DEBUG",
        console=True
    )
    
    log_file = get_log_file_path()
    print(f"Log file will be written to: {log_file}")
    
    # Simulate a pipeline task
    task_id = "T006_DEMO"
    config = {
        "chunk_size": 1000,
        "random_seed": 42,
        "enable_sampling": True
    }
    
    start_time = time.time()
    
    try:
        # Log start
        log_pipeline_start(task_id, config)
        logger.debug("Initializing demo components...")
        
        # Simulate processing steps
        logger.info("Step 1: Loading configuration...")
        time.sleep(0.1)
        
        logger.info("Step 2: Processing data chunks...")
        log_metric(task_id, "chunks_processed", 5, unit="count")
        log_metric(task_id, "records_processed", 5000, unit="rows")
        
        time.sleep(0.1)
        
        logger.info("Step 3: Computing metrics...")
        log_metric(task_id, "computation_time", 0.45, unit="seconds")
        
        # Simulate a warning
        logger.warning("Warning: Some data points were excluded due to missing values.")
        log_metric(task_id, "excluded_records", 12, unit="rows")
        
        # Simulate successful completion
        duration = time.time() - start_time
        log_pipeline_end(task_id, "SUCCESS", duration_seconds=duration)
        
        print(f"\nDemo completed successfully in {duration:.2f} seconds.")
        print(f"Check the log file at: {log_file}")
        
    except Exception as e:
        duration = time.time() - start_time
        log_error(task_id, e, context={"step": "demo_execution"})
        log_pipeline_end(task_id, "FAILED", duration_seconds=duration)
        print(f"\nDemo failed: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
