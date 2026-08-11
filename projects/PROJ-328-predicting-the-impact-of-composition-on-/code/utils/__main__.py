"""
Entry point for testing the Utils module.
Runs self-tests for error handling and warning injection.
"""
import sys
import logging
from pathlib import Path

from utils.logging_config import setup_logging, get_logger
from utils.error_handlers import (
    SolderPipelineError,
    ConfigurationError,
    DataValidationError,
    IngestionError,
    ModelTrainingError
)
from utils.fr007_warnings import main as run_warning_tests

def test_error_handling():
    """Tests the custom exception hierarchy."""
    logger = get_logger(__name__)
    logger.info("Testing custom error handlers...")
    
    try:
        raise ConfigurationError("Test config error", {"key": "value"})
    except SolderPipelineError as e:
        assert e.message == "Configuration Error: Test config error"
        assert e.details == {"key": "value"}
        logger.info("ConfigurationError hierarchy test passed.")
    
    try:
        raise DataValidationError("Test data error")
    except SolderPipelineError as e:
        assert "Data Validation Error" in str(e)
        logger.info("DataValidationError hierarchy test passed.")
    
    try:
        raise IngestionError("Test ingestion error")
    except SolderPipelineError as e:
        assert "Ingestion Error" in str(e)
        logger.info("IngestionError hierarchy test passed.")
    
    try:
        raise ModelTrainingError("Test training error")
    except SolderPipelineError as e:
        assert "Model Training Error" in str(e)
        logger.info("ModelTrainingError hierarchy test passed.")
    
    logger.info("All error handler tests passed.")
    return True

def main():
    """Main entry point for utils testing."""
    # Ensure logging is set up
    setup_logging()
    logger = get_logger(__name__)
    
    logger.info("Starting Utils Module Self-Tests...")
    
    success = True
    try:
        if not test_error_handling():
            success = False
    except Exception as e:
        logger.error(f"Error handler test failed: {e}", exc_info=True)
        success = False
    
    try:
        if not run_warning_tests():
            success = False
    except Exception as e:
        logger.error(f"Warning injection test failed: {e}", exc_info=True)
        success = False
    
    if success:
        logger.info("Utils Module Self-Tests: PASSED")
        return 0
    else:
        logger.error("Utils Module Self-Tests: FAILED")
        return 1

if __name__ == "__main__":
    sys.exit(main())