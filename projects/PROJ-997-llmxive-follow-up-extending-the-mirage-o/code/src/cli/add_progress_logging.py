import json
import logging
import sys
from pathlib import Path
from src.config.logging_config import setup_logger, log_sample_progress, ensure_log_dir

def main():
    """
    Entry point for T017: Add logging for data generation progress.
    
    This script configures the logger to write JSON lines to logs/pipeline.log.
    It demonstrates the logging mechanism by processing a small set of mock samples
    to ensure the log file is created with the correct schema before T015 runs.
    
    Note: In the actual T015 pipeline, this logging logic is called for every sample.
    This script serves as a setup/verification step to ensure the logging infrastructure
    is ready and produces the required output format.
    """
    # Ensure logs directory exists
    ensure_log_dir()
    
    # Setup the logger specifically for pipeline progress (JSON lines format)
    logger = setup_logger("pipeline_progress")
    
    # Define the log file path
    log_file_path = Path("logs/pipeline.log")
    
    # Log a startup entry
    logger.info(json.dumps({
        "sample_id": "pipeline_start",
        "status": "success",
        "message": "Progress logging initialized for data generation pipeline"
    }))
    
    # Simulate processing a few samples to verify the log format
    # In T015, this loop would iterate over the actual dataset stream
    mock_samples = [
        {"id": "mock_001", "prompt": "Test prompt 1"},
        {"id": "mock_002", "prompt": "Test prompt 2"},
        {"id": "mock_003", "prompt": "Test prompt 3"},
    ]
    
    for sample in mock_samples:
        sample_id = sample["id"]
        try:
            # Simulate a successful processing step
            # In T015, this would be the actual feature extraction + inference call
            log_sample_progress(
                logger, 
                sample_id=sample_id, 
                status="success", 
                error_code=None
            )
        except Exception as e:
            # Simulate an error case
            log_sample_progress(
                logger,
                sample_id=sample_id,
                status="error",
                error_code=str(type(e).__name__)
            )
    
    # Log a completion entry
    logger.info(json.dumps({
        "sample_id": "pipeline_demo_complete",
        "status": "success",
        "message": "Demo logging sequence completed. logs/pipeline.log is ready for T015."
    }))
    
    print(f"Logging verification complete. Check {log_file_path} for JSON lines output.")

if __name__ == "__main__":
    main()
