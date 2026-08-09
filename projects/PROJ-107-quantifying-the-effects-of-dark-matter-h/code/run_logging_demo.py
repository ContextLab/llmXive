"""
Demo script to verify the logging infrastructure (Task T006).
This script exercises the logging functions and writes to disk.
"""
import sys
import time
from pathlib import Path

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.logging import (
    get_pipeline_logger,
    log_pipeline_start,
    log_pipeline_end,
    log_error,
    log_metric,
    log_chunk_info
)

def main():
    logger = get_pipeline_logger("demo")
    
    # Log start
    log_pipeline_start(logger, task_id="T006-DEMO")
    
    try:
        # Simulate some work
        log_metric(logger, "start_time", time.time(), "epoch")
        
        for i in range(3):
            time.sleep(0.1)  # Simulate processing
            log_chunk_info(logger, i, 3, 100, 0.1)
        
        log_metric(logger, "end_time", time.time(), "epoch")
        log_metric(logger, "total_duration", 0.3, "seconds")
        
        # Simulate a non-fatal warning context
        log_error(logger, ValueError("Simulated warning for demo"), {"stage": "validation", "item": "test_001"})
        
        log_pipeline_end(logger, success=True)
        
    except Exception as e:
        log_error(logger, e, {"stage": "demo_execution"})
        log_pipeline_end(logger, success=False)
        raise

if __name__ == "__main__":
    main()
