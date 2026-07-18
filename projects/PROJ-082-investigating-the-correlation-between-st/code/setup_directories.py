import os
import sys
from pathlib import Path
from utils.logger import get_logger

def create_directories():
    """
    Initialize project directory structure.
    Creates: code/, tests/, data/, docs/
    """
    logger = get_logger(__name__)
    project_root = Path(__file__).resolve().parent.parent

    directories = [
        "code",
        "tests",
        "data",
        "docs"
    ]

    created_count = 0
    for dir_name in directories:
        dir_path = project_root / dir_name
        try:
            dir_path.mkdir(parents=True, exist_ok=True)
            logger.info(f"Directory created/verified: {dir_path}")
            created_count += 1
        except OSError as e:
            logger.error(f"Failed to create directory {dir_path}: {e}")
            raise

    logger.info(f"Successfully initialized {created_count} project directories.")
    return created_count

def verify_structure():
    """
    Verify that the required project directories exist.
    """
    logger = get_logger(__name__)
    project_root = Path(__file__).resolve().parent.parent

    required_dirs = ["code", "tests", "data", "docs"]
    missing = []

    for dir_name in required_dirs:
        dir_path = project_root / dir_name
        if not dir_path.is_dir():
            missing.append(dir_name)
        else:
            logger.debug(f"Verified existence: {dir_path}")

    if missing:
        logger.error(f"Missing required directories: {missing}")
        return False

    logger.info("Project directory structure verified successfully.")
    return True

def main():
    """
    Entry point for directory initialization script.
    """
    logger = get_logger(__name__)
    logger.info("Starting project directory initialization...")

    try:
        create_directories()
        if verify_structure():
            logger.info("Initialization complete.")
            return 0
        else:
            logger.error("Verification failed.")
            return 1
    except Exception as e:
        logger.error(f"Initialization failed: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
