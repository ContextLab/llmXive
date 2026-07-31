import os
import sys
import logging
from pathlib import Path
from utils.logging import get_logger
from utils.config import get_project_root

def create_tests_directories(logger: logging.Logger) -> None:
    """
    Creates the required directory structure for tests.
    
    Structure:
    - tests/
      - contract/
      - unit/
      - integration/
    
    Args:
        logger: Logger instance for logging creation status.
    """
    project_root = get_project_root()
    tests_root = project_root / "tests"
    
    directories = [
        tests_root,
        tests_root / "contract",
        tests_root / "unit",
        tests_root / "integration",
    ]
    
    for dir_path in directories:
        if not dir_path.exists():
            dir_path.mkdir(parents=True, exist_ok=True)
            logger.info(f"Created directory: {dir_path}")
        else:
            logger.debug(f"Directory already exists: {dir_path}")

def main() -> None:
    """Main entry point for creating test directory structure."""
    logger = get_logger("setup_tests_structure")
    logger.info("Starting test directory structure creation...")
    
    try:
        create_tests_directories(logger)
        logger.info("Test directory structure creation completed successfully.")
    except Exception as e:
        logger.error(f"Failed to create test directory structure: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
