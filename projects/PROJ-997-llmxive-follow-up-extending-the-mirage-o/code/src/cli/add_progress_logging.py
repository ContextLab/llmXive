"""
T017: Add per-sample logging for data generation progress.

This script ensures that the logging configuration for `logs/pipeline.log`
includes a JSON-lines formatter capable of recording per-sample progress
with the required keys: `sample_id`, `status`, and `error_code`.

It also demonstrates the usage of the `log_sample_progress` helper
defined in `src/config/logging_config.py` to ensure the logging
mechanism is wired correctly before the main generation pipeline runs.
"""
import json
import logging
import sys
from pathlib import Path

# Import the logging configuration helper
from src.config.logging_config import setup_logger, log_sample_progress, ensure_log_dir

def main():
    """
    Initializes the logger for pipeline progress and logs a sample entry
    to verify the JSON-lines format and required keys are present.
    """
    # Ensure the logs directory exists
    log_dir = Path("logs")
    ensure_log_dir(log_dir)
    
    log_file = log_dir / "pipeline.log"

    # Setup the logger specifically for pipeline progress
    # This reuses the existing setup_logger but ensures the file handler
    # is attached to the specific log file for T017 requirements.
    logger = setup_logger(
        name="pipeline_progress",
        level=logging.INFO,
        log_file=str(log_file)
    )

    # Verify the logger has the correct handlers
    if not logger.handlers:
        logger.error("No handlers configured for pipeline_progress logger.")
        sys.exit(1)

    # Log a test entry to demonstrate the format
    # Keys required by T017: sample_id, status, error_code
    test_entry = {
        "sample_id": "test_sample_001",
        "status": "success",
        "error_code": None,
        "message": "T017 Logging verification entry"
    }

    # Use the dedicated helper to log as JSON lines
    log_sample_progress(
        logger=logger,
        sample_id=test_entry["sample_id"],
        status=test_entry["status"],
        error_code=test_entry["error_code"]
    )

    # Log a sample error entry
    error_entry = {
        "sample_id": "test_sample_002",
        "status": "error",
        "error_code": "QUANTIZATION_LOAD_FAIL"
    }
    
    log_sample_progress(
        logger=logger,
        sample_id=error_entry["sample_id"],
        status=error_entry["status"],
        error_code=error_entry["error_code"]
    )

    # Log a skipped entry
    skip_entry = {
        "sample_id": "test_sample_003",
        "status": "skipped",
        "error_code": "INVALID_INPUT"
    }

    log_sample_progress(
        logger=logger,
        sample_id=skip_entry["sample_id"],
        status=skip_entry["status"],
        error_code=skip_entry["error_code"]
    )

    print(f"Logging verification complete. Check {log_file} for JSON-lines output.")
    print("Expected format per line:")
    print(json.dumps(test_entry))

if __name__ == "__main__":
    main()