"""
Main entry point for testing utility module functionality.
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
    ModelTrainingError,
    DataInsufficientError,
    CompositionSumError
)
from utils.fr007_warnings import main as run_warning_tests

def test_error_handling():
    """Test that all custom exceptions work correctly."""
    logger = get_logger(__name__)
    logger.info("Testing error handling...")
    
    # Test base exception
    try:
        raise SolderPipelineError("Base error test")
    except SolderPipelineError as e:
        logger.info(f"Caught SolderPipelineError: {e.message}")
    
    # Test ConfigurationError
    try:
        raise ConfigurationError("Missing config", config_key="data_path")
    except ConfigurationError as e:
        logger.info(f"Caught ConfigurationError: {e.message}")
    
    # Test DataValidationError
    try:
        raise DataValidationError("Invalid value", record_id="123", field="hardness")
    except DataValidationError as e:
        logger.info(f"Caught DataValidationError: {e.message}")
    
    # Test IngestionError
    try:
        raise IngestionError("API failed", source="materials_project")
    except IngestionError as e:
        logger.info(f"Caught IngestionError: {e.message}")
    
    # Test ModelTrainingError
    try:
        raise ModelTrainingError("Convergence failed", model_type="xgboost")
    except ModelTrainingError as e:
        logger.info(f"Caught ModelTrainingError: {e.message}")
    
    # Test DataInsufficientError
    try:
        raise DataInsufficientError("Too few samples", current_n=30, required_n=50)
    except DataInsufficientError as e:
        logger.info(f"Caught DataInsufficientError: {e.message}")
    
    # Test CompositionSumError
    try:
        raise CompositionSumError("Sum below threshold", record_id="456", actual_sum=92.5, threshold=95.0)
    except CompositionSumError as e:
        logger.info(f"Caught CompositionSumError: {e.message}")
    
    logger.info("Error handling tests completed successfully!")

def main():
    """Main entry point for utility testing."""
    setup_logging()
    logger = get_logger(__name__)
    
    logger.info("Running utility module tests...")
    
    test_error_handling()
    run_warning_tests()
    
    logger.info("All utility tests passed!")

if __name__ == "__main__":
    main()