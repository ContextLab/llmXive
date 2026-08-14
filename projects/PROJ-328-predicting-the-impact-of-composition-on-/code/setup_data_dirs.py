import os
import sys
import logging
from pathlib import Path
from utils.logging_config import get_logger

def setup_data_directories():
    """
    Ensure all data directories exist with proper structure.
    """
    logger = get_logger(__name__)
    project_root = Path(__file__).resolve().parent.parent

    data_dirs = [
        "data/raw",
        "data/processed",
        "data/outputs",
        "data/config",
        "data/checksums",
    ]

    for dir_path in data_dirs:
        full_path = project_root / dir_path
        full_path.mkdir(parents=True, exist_ok=True)
        logger.info(f"Ensured data directory: {full_path}")

    return True

def verify_directory_structure():
    """
    Verify that all required directories exist.
    """
    logger = get_logger(__name__)
    project_root = Path(__file__).resolve().parent.parent

    required_dirs = [
        "data/raw",
        "data/processed",
        "data/outputs",
        "data/config",
        "data/checksums",
        "code/ingestion",
        "code/features",
        "code/models",
        "code/evaluation",
        "code/visualization",
        "code/utils",
        "tests/contract",
        "tests/integration",
        "tests/unit",
    ]

    missing = []
    for dir_path in required_dirs:
        full_path = project_root / dir_path
        if not full_path.exists():
            missing.append(str(full_path))
            logger.warning(f"Missing directory: {full_path}")

    if missing:
        logger.error(f"Missing {len(missing)} directories")
        return False
    
    logger.info("All required directories verified")
    return True

def main():
    logger = get_logger(__name__)
    logger.info("Setting up data directories...")
    
    setup_data_directories()
    
    if verify_directory_structure():
        logger.info("Setup complete")
        return 0
    else:
        logger.error("Setup failed - missing directories")
        return 1

if __name__ == "__main__":
    sys.exit(main())
