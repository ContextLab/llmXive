"""
Main entry point for testing and running utility modules.

This script allows running utility tests or demonstrations from the command line.
"""
import sys
import logging
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.logging_config import setup_logging, get_logger
from utils.error_handlers import (
    SolderPipelineError,
    ConfigurationError,
    DataValidationError,
    IngestionError,
    ModelTrainingError,
    DataInsufficientError
)
from utils.fr007_warnings import main as run_warning_tests

logger = get_logger(__name__)


def test_error_handling() -> None:
    """Test the custom error handling infrastructure."""
    logger.info("Testing error handling infrastructure...")

    try:
        # Test ConfigurationError
        raise ConfigurationError(
            "Missing required configuration key",
            config_file="data/config/sources.yaml",
            key="materials_project_api_key"
        )
    except ConfigurationError as e:
        logger.error(f"Caught expected ConfigurationError: {e.message}")

    try:
        # Test DataValidationError
        raise DataValidationError(
            "Elemental composition sum out of range",
            record_id="rec_001",
            field="composition_sum"
        )
    except DataValidationError as e:
        logger.error(f"Caught expected DataValidationError: {e.message}")

    try:
        # Test IngestionError
        raise IngestionError(
            "Failed to fetch data from source",
            source="Materials Project API",
            error_code=403
        )
    except IngestionError as e:
        logger.error(f"Caught expected IngestionError: {e.message}")

    try:
        # Test ModelTrainingError
        raise ModelTrainingError(
            "Model training failed due to convergence issues",
            model_type="XGBoost",
            stage="fit"
        )
    except ModelTrainingError as e:
        logger.error(f"Caught expected ModelTrainingError: {e.message}")

    try:
        # Test DataInsufficientError
        raise DataInsufficientError(
            "Dataset size below minimum threshold",
            current_count=30,
            minimum_required=50
        )
    except DataInsufficientError as e:
        logger.error(f"Caught expected DataInsufficientError: {e.message}")

    logger.info("Error handling tests completed successfully.")


def main() -> None:
    """Main entry point for the utility module."""
    setup_logging()
    logger.info("Starting utility module tests...")

    test_error_handling()
    run_warning_tests()

    logger.info("All utility tests passed.")


if __name__ == "__main__":
    main()