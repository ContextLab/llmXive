import os
import sys
import logging
from typing import List
from config import ensure_directories, get_config

def setup_script_logging() -> logging.Logger:
    """
    Setup logging for the script.
    Returns a logger instance configured for the project.
    """
    logger = logging.getLogger("setup_directories")
    logger.setLevel(logging.INFO)
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
        logger.addHandler(handler)
    return logger

def create_directories(logger: logging.Logger) -> None:
    """
    Create the required project directories: code, artifacts, tests.
    Also ensures subdirectories defined in config are present.
    """
    config = get_config()
    base_dirs = [
        os.path.join(os.path.dirname(os.path.dirname(__file__)), "code"),
        os.path.join(os.path.dirname(os.path.dirname(__file__)), "artifacts"),
        os.path.join(os.path.dirname(os.path.dirname(__file__)), "tests")
    ]

    # Ensure directories exist via config utility as well
    ensure_directories(config)

    for dir_path in base_dirs:
        if not os.path.exists(dir_path):
            os.makedirs(dir_path)
            logger.info(f"Created directory: {dir_path}")
        else:
            logger.info(f"Directory already exists: {dir_path}")

def main() -> None:
    """
    Main entry point for the directory setup script.
    """
    logger = setup_script_logging()
    logger.info("Starting directory setup...")
    create_directories(logger)
    logger.info("Directory setup completed successfully.")

if __name__ == "__main__":
    main()
