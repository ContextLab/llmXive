import os
import sys
from pathlib import Path
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parent.parent
PROJECT_DIR = PROJECT_ROOT / "projects" / "PROJ-967-llmxive-follow-up-extending-beyond-scala"

REQUIRED_DIRS = [
    "data/raw",
    "data/processed",
    "code",
    "tests",
    "results"
]

def ensure_directory(dir_path: Path) -> bool:
    """
    Ensure a directory exists, creating it if necessary.
    
    Args:
        dir_path: Path object representing the directory to create
        
    Returns:
        bool: True if directory exists or was created successfully, False otherwise
    """
    try:
        dir_path.mkdir(parents=True, exist_ok=True)
        logger.info(f"Directory ensured: {dir_path}")
        return True
    except Exception as e:
        logger.error(f"Failed to create directory {dir_path}: {e}")
        return False

def main():
    """
    Main function to create all required project directories.
    """
    logger.info(f"Starting directory creation for project: {PROJECT_DIR}")
    
    success_count = 0
    total_count = len(REQUIRED_DIRS)
    
    for dir_name in REQUIRED_DIRS:
        full_path = PROJECT_DIR / dir_name
        if ensure_directory(full_path):
            success_count += 1
    
    logger.info(f"Directory creation complete: {success_count}/{total_count} directories created successfully")
    
    if success_count == total_count:
        logger.info("All required directories have been created.")
        return 0
    else:
        logger.error(f"Failed to create {total_count - success_count} directories.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
