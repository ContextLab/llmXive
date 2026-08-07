"""
Main entry point for the utils package.

This script serves as a demonstration and validation runner for the
error handling and logging infrastructure.
"""
import sys
import logging
from pathlib import Path
from utils.logging_config import setup_logging, get_logger
from utils.error_handlers import (
    SolderPipelineError,
    DataValidationError,
    IngestionError,
    ModelTrainingError,
    ConfigurationError
)
from utils.fr007_warnings import main as run_warning_tests
from utils.__init__ import * # Import all public names


def main():
    """
    Main entry point for validating the utility infrastructure.
    """
    # Setup logging
    log_path = "data/outputs/utils_validation.log"
    logger = setup_logging(log_path)
    logger = get_logger(__name__)
    
    logger.info("Starting validation of error handling and logging infrastructure...")
    
    # Test 1: Exception hierarchy
    try:
        raise DataValidationError("Test validation error", {"field": "hardness"})
    except SolderPipelineError as e:
        logger.info(f"Caught expected SolderPipelineError: {e}")
    except Exception as e:
        logger.error(f"Unexpected exception type: {type(e)}, {e}")
    
    try:
        raise IngestionError("Test ingestion error")
    except SolderPipelineError as e:
        logger.info(f"Caught expected IngestionError: {e}")
    
    try:
        raise ModelTrainingError("Test model error")
    except SolderPipelineError as e:
        logger.info(f"Caught expected ModelTrainingError: {e}")
    
    try:
        raise ConfigurationError("Test config error")
    except SolderPipelineError as e:
        logger.info(f"Caught expected ConfigurationError: {e}")
    
    # Test 2: Logger functionality
    test_logger = get_logger("test.module")
    test_logger.debug("Debug message")
    test_logger.info("Info message")
    test_logger.warning("Warning message")
    test_logger.error("Error message")
    
    # Test 3: FR-007 Warnings
    logger.info("Running FR-007 warning tests...")
    run_warning_tests()
    
    logger.info("Validation of error handling and logging infrastructure completed successfully.")
    
    print(f"Validation log written to: {log_path}")


if __name__ == "__main__":
    main()
