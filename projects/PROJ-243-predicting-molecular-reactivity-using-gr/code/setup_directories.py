import os
import sys
import logging
from typing import List
from config import get_config, ensure_directories

def setup_script_logging() -> logging.Logger:
    """Initialize script-level logging."""
    logger = logging.getLogger(__name__)
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    return logger

def create_directories(config: dict, logger: logging.Logger) -> None:
    """
    Create the required project directories: code, artifacts, tests.
    
    This task (T002) specifically targets the creation of these three
    top-level directories to structure the project's source code,
    generated artifacts, and test suites.
    """
    required_dirs = [
        "code",
        "artifacts",
        "tests"
    ]

    # Ensure base directories from config exist first (data/processed, etc.)
    # as a safety measure, though T001 tasks should have handled data dirs.
    ensure_directories(config, logger)

    for dir_path in required_dirs:
        full_path = os.path.join(config["project_root"], dir_path)
        if not os.path.exists(full_path):
            os.makedirs(full_path)
            logger.info(f"Created directory: {full_path}")
        else:
            logger.info(f"Directory already exists: {full_path}")

def main() -> int:
    """Main entry point for T002: Create code and artifact directories."""
    logger = setup_script_logging()
    logger.info("Starting T002: Creating code and artifact directories...")
    
    try:
        config = get_config()
        create_directories(config, logger)
        logger.info("T002 completed successfully.")
        return 0
    except Exception as e:
        logger.error(f"Failed to create directories: {e}", exc_info=True)
        return 1

if __name__ == "__main__":
    sys.exit(main())
