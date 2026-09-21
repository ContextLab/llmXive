import os
import sys
import logging
from typing import List
from config import get_config, ensure_directories

def setup_script_logging(name: str = "setup_directories") -> logging.Logger:
    """Initialize logging for the directory setup script."""
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger
    logger.setLevel(logging.INFO)
    handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    return logger

def create_directories(config: dict, logger: logging.Logger) -> None:
    """
    Create the required project directories based on configuration.
    
    This script implements T002 by ensuring the existence of:
    - code/
    - artifacts/
    - tests/
    
    It also relies on `config.ensure_directories` to create data subdirectories
    (data/raw, data/processed, data/assets) which were defined in T001.
    """
    # Define the root directories required for T002
    root_dirs = [
        "code",
        "artifacts",
        "tests",
    ]

    for dir_path in root_dirs:
        if not os.path.exists(dir_path):
            os.makedirs(dir_path, exist_ok=True)
            logger.info(f"Created directory: {dir_path}")
        else:
            logger.info(f"Directory already exists: {dir_path}")

    # Ensure data subdirectories exist as per T001a, T001b, T001c
    # This uses the utility from config.py which is already established
    data_dirs = [
        "data/raw",
        "data/processed",
        "data/assets"
    ]
    
    for dir_path in data_dirs:
        if not os.path.exists(dir_path):
            os.makedirs(dir_path, exist_ok=True)
            logger.info(f"Created data directory: {dir_path}")
        else:
            logger.info(f"Data directory already exists: {dir_path}")

def main() -> int:
    """Main entry point for directory setup."""
    logger = setup_script_logging()
    logger.info("Starting directory setup (Task T002)...")
    
    try:
        config = get_config()
        create_directories(config, logger)
        
        # Verify existence
        required_dirs = ["code", "artifacts", "tests", "data/raw", "data/processed", "data/assets"]
        missing = [d for d in required_dirs if not os.path.exists(d)]
        
        if missing:
            logger.error(f"Failed to create required directories: {missing}")
            return 1
        
        logger.info("Directory setup completed successfully.")
        return 0
    except Exception as e:
        logger.error(f"Error during directory setup: {e}", exc_info=True)
        return 1

if __name__ == "__main__":
    sys.exit(main())
