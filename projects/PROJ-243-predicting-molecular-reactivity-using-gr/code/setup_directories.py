import os
import sys
import logging
from typing import List
from config import get_config, ensure_directories

def setup_script_logging() -> logging.Logger:
    """
    Initialize logging for the setup script.
    Returns a logger instance configured for the current run.
    """
    logger = logging.getLogger("setup_directories")
    logger.setLevel(logging.INFO)
    
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        ))
        logger.addHandler(handler)
    
    return logger

def create_directories(dir_paths: List[str], logger: logging.Logger) -> None:
    """
    Create the specified directories if they do not exist.
    
    Args:
        dir_paths: List of relative directory paths to create.
        logger: Logger instance for status updates.
    """
    for dir_path in dir_paths:
        if not os.path.exists(dir_path):
            os.makedirs(dir_path, exist_ok=True)
            logger.info(f"Created directory: {dir_path}")
        else:
            logger.info(f"Directory already exists: {dir_path}")

def main() -> int:
    """
    Main entry point for creating project directories.
    
    This script creates the standard project structure:
    - code/
    - artifacts/
    - tests/
    
    Returns:
        0 on success, 1 on failure.
    """
    logger = setup_script_logging()
    logger.info("Starting directory setup...")
    
    try:
        # Define the directories required for T002
        required_dirs = [
            "code",
            "artifacts",
            "tests"
        ]
        
        # Create directories
        create_directories(required_dirs, logger)
        
        # Also ensure subdirectories for artifacts (logs, weights, etc.)
        # as they are referenced in later tasks
        artifact_subdirs = [
            "artifacts/logs",
            "artifacts/weights",
            "artifacts/metrics.json", # This is a file, but the parent dir is needed
            "artifacts/splits"
        ]
        create_directories(artifact_subdirs, logger)
        
        # Ensure tests subdirectories exist
        test_subdirs = [
            "tests/unit",
            "tests/integration",
            "tests/contract"
        ]
        create_directories(test_subdirs, logger)
        
        logger.info("Directory setup completed successfully.")
        return 0
        
    except Exception as e:
        logger.error(f"Failed to create directories: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
