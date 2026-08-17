"""
Script to initialize the project directory structure.
Creates required folders for code, artifacts, and tests as per T002.
"""
import os
import sys
import logging
from typing import List
from config import ensure_directories, get_config

def setup_script_logging() -> logging.Logger:
    """Initialize logging for the setup script."""
    logger = logging.getLogger("setup_directories")
    logger.setLevel(logging.INFO)
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        ))
        logger.addHandler(handler)
    return logger

def create_directories(logger: logging.Logger) -> None:
    """
    Create the standard project directories required by T002.
    Targets: code, artifacts, tests (relative to project root).
    Also ensures data subdirectories exist via config.
    """
    config = get_config()
    base_dirs = config.get("base_dirs", [])
    
    # Explicitly define the T002 required directories
    # We assume the project root is the current working directory
    required_dirs = [
        "code",
        "artifacts",
        "tests"
    ]

    # Add data subdirectories if not already handled by ensure_directories
    # (T001 tasks handle data/ structure, but we ensure the root exists)
    data_dirs = [
        "data",
        "data/raw",
        "data/processed",
        "data/assets"
    ]

    all_dirs_to_create = required_dirs + data_dirs

    for dir_path in all_dirs_to_create:
        abs_path = os.path.abspath(dir_path)
        if not os.path.exists(abs_path):
            os.makedirs(abs_path, exist_ok=True)
            logger.info(f"Created directory: {abs_path}")
        else:
            logger.debug(f"Directory already exists: {abs_path}")

    # Use the existing config utility to ensure other paths defined in spec are ready
    # This covers artifacts/logs, etc., if defined in config
    try:
        ensure_directories(config, logger)
    except Exception as e:
        logger.error(f"Error ensuring directories from config: {e}")
        # Continue as core T002 dirs might still be created

def main() -> None:
    """Entry point for the directory setup script."""
    logger = setup_script_logging()
    logger.info("Starting directory setup for project (T002)...")
    
    try:
        create_directories(logger)
        logger.info("Directory setup completed successfully.")
    except Exception as e:
        logger.critical(f"Failed to create directories: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
