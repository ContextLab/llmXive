import logging
import sys
from pathlib import Path

from utils.logging import get_logger, configure_root_logger
from utils.config import get_project_root


def create_directories(logger: logging.Logger) -> None:
    """
    Create the required directory structure for data storage.
    
    This function creates:
    - data/raw/
    - data/processed/
    
    Args:
        logger: Logger instance for logging operations.
    """
    project_root = get_project_root()
    data_root = project_root / "data"
    
    raw_dir = data_root / "raw"
    processed_dir = data_root / "processed"
    
    # Create directories with exist_ok=True to avoid errors if they already exist
    raw_dir.mkdir(parents=True, exist_ok=True)
    processed_dir.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"Created directory: {raw_dir}")
    logger.info(f"Created directory: {processed_dir}")
    
    # Verification step as per requirements
    assert raw_dir.is_dir(), f"Failed to create directory: {raw_dir}"
    assert processed_dir.is_dir(), f"Failed to create directory: {processed_dir}"
    
    logger.info("Directory structure verification passed.")


def main() -> int:
    """
    Main entry point for the directory creation script.
    
    Returns:
        int: 0 on success, 1 on failure.
    """
    configure_root_logger()
    logger = get_logger(__name__)
    
    try:
        logger.info("Starting directory creation process.")
        create_directories(logger)
        logger.info("Directory creation process completed successfully.")
        return 0
    except AssertionError as e:
        logger.error(f"Directory verification failed: {e}")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error during directory creation: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())