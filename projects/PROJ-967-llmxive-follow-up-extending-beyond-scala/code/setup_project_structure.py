"""
Setup script to create the project directory structure for llmXive follow-up.
Creates data/raw, data/processed, results, code, and tests directories.
"""
import os
import sys
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parent.parent
PROJECT_NAME = "PROJ-967-llmxive-follow-up-extending-beyond-scala"
PROJECT_DIR = PROJECT_ROOT / "projects" / PROJECT_NAME

DIRECTORIES_TO_CREATE = [
    "data/raw",
    "data/processed",
    "results",
    "code",
    "tests"
]

def ensure_directory(path: Path) -> bool:
    """
    Ensure a directory exists, creating it if necessary.
    
    Args:
        path: Path object representing the directory to create.
        
    Returns:
        True if directory exists or was created successfully, False otherwise.
    """
    try:
        path.mkdir(parents=True, exist_ok=True)
        logger.info(f"Created directory: {path}")
        return True
    except Exception as e:
        logger.error(f"Failed to create directory {path}: {e}")
        return False

def main():
    """
    Main entry point to create the project directory structure.
    """
    logger.info(f"Starting project structure setup for {PROJECT_NAME}")
    
    # Create the project root directory
    if not ensure_directory(PROJECT_DIR):
        logger.error("Failed to create project root directory. Exiting.")
        sys.exit(1)
    
    created_count = 0
    failed_count = 0
    
    for dir_name in DIRECTORIES_TO_CREATE:
        dir_path = PROJECT_DIR / dir_name
        if ensure_directory(dir_path):
            created_count += 1
        else:
            failed_count += 1
    
    logger.info(f"Directory creation complete: {created_count} created, {failed_count} failed")
    
    if failed_count > 0:
        logger.error("Some directories failed to create.")
        sys.exit(1)
    else:
        logger.info("All required directories created successfully.")
        sys.exit(0)

if __name__ == "__main__":
    main()