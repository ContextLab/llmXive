"""
Runner script to demonstrate and verify the logging and error handling infrastructure.
This script ensures the logging configuration is applied and errors are caught correctly.
"""
import sys
import os
from pathlib import Path

# Ensure src is in path
src_path = Path(__file__).parent
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

from logging_config import configure_logging, get_logger, SafeExecutionBlock, DataIngestionError, PipelineError
from error_utils import validate_not_null, safe_divide

def main():
    # 1. Configure global logging
    configure_logging(log_level=10) # DEBUG
    logger = get_logger("logging_setup_runner")

    logger.info("Starting logging infrastructure verification.")

    # 2. Test SafeExecutionBlock
    with SafeExecutionBlock("test_division", logger):
        result = safe_divide(10.0, 2.0, context="test_division")
        logger.info(f"Safe division result: {result}")

    # 3. Test error handling with a deliberate error
    try:
        with SafeExecutionBlock("test_null_validation", logger):
            validate_not_null(None, "test_field", "test_null_validation")
    except DataIngestionError as e:
        logger.info(f"Caught expected DataIngestionError: {e}")

    # 4. Test generic exception wrapping
    try:
        with SafeExecutionBlock("test_generic_error", logger):
            raise ValueError("This is a generic error")
    except PipelineError as e:
        logger.info(f"Caught wrapped PipelineError: {e}")

    logger.info("Logging infrastructure verification complete.")

if __name__ == "__main__":
    main()