"""
CLI entry point for utility module testing and configuration.
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


def test_error_handling():
    """Test that custom exceptions work as expected."""
    logger = get_logger("utils_test")
    
    logger.info("Testing custom exception hierarchy...")
    
    try:
        try:
            raise ConfigurationError("Missing config key", {"key": "API_KEY"})
        except ConfigurationError as e:
            logger.warning(f"Caught ConfigurationError: {e}")
        
        try:
            raise DataValidationError("Invalid composition sum", {"sum": 0.9, "expected": 1.0})
        except DataValidationError as e:
            logger.warning(f"Caught DataValidationError: {e}")
        
        try:
            raise IngestionError("Failed to fetch from NIST", {"source": "NIST", "status": 404})
        except IngestionError as e:
            logger.warning(f"Caught IngestionError: {e}")
        
        try:
            raise ModelTrainingError("XGBoost failed to converge", {"iterations": 1000})
        except ModelTrainingError as e:
            logger.warning(f"Caught ModelTrainingError: {e}")
        
        logger.info("All exception tests passed.")
    
    except Exception as e:
        logger.error(f"Unexpected error during test: {e}")
        raise


def main():
    """Main entry point for utility module."""
    # Initialize logging
    project_root = Path(__file__).resolve().parent.parent.parent
    setup_logging(project_root=project_root)
    logger = get_logger("utils_main")
    
    logger.info("Starting utility module CLI...")
    
    # Run tests
    test_error_handling()
    
    # Run FR007 warning tests
    run_warning_tests()
    
    logger.info("Utility module CLI completed successfully.")


if __name__ == "__main__":
    main()
