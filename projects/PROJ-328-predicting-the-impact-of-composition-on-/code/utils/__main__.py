"""
Entry point for testing the logging and error handling utilities.
Run with: python -m code.utils
"""
import sys
import logging

# Add project root to path if running as script
if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from pathlib import Path
from utils.logging_config import setup_logging, get_logger
from utils.error_handlers import (
    SolderPipelineError,
    DataValidationError,
    IngestionError,
)

def main():
    """Test the logging and error handling infrastructure."""
    # Setup logging to both console and a test log file
    log_file = Path("logs/test_run.log")
    setup_logging(level="DEBUG", log_file=str(log_file), console=True)

    logger = get_logger("T008_TEST")
    logger.info("Testing logging configuration...")

    # Test different log levels
    logger.debug("This is a DEBUG message")
    logger.info("This is an INFO message")
    logger.warning("This is a WARNING message")
    logger.error("This is an ERROR message")

    # Test custom exceptions
    try:
        raise DataValidationError(
            "Invalid hardness value",
            field="hardness",
            value="-5.0",
            expected="positive number",
        )
    except DataValidationError as e:
        logger.error(f"Caught DataValidationError: {e}")

    try:
        raise IngestionError(
            "Failed to fetch data from source",
            source="https://example.com/api",
            status_code=404,
        )
    except IngestionError as e:
        logger.error(f"Caught IngestionError: {e}")

    try:
        raise SolderPipelineError("General pipeline failure")
    except SolderPipelineError as e:
        logger.error(f"Caught SolderPipelineError: {e}")

    logger.info("All tests passed successfully!")
    print(f"\nLogs written to: {log_file.resolve()}")

if __name__ == "__main__":
    main()