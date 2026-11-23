import os
import sys
from pathlib import Path
import logging

# Configure basic logging for this script
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def create_directory(path: str) -> bool:
    """
    Creates a directory at the specified path if it does not already exist.
    
    Args:
        path: The directory path to create.
        
    Returns:
        True if the directory was created or already exists, False otherwise.
    """
    dir_path = Path(path)
    try:
        dir_path.mkdir(parents=True, exist_ok=True)
        logger.info(f"Directory created or confirmed: {dir_path}")
        return True
    except OSError as e:
        logger.error(f"Failed to create directory {dir_path}: {e}")
        return False

def main():
    """
    Main entry point to create the project directory structure.
    """
    # Define the required directory structure relative to project root
    # Assuming the script is run from the project root or the path is relative to it
    base_dirs = [
        "data/raw",
        "data/interim",
        "data/results",
        "data/processed",
        "code",
        "tests/unit",
        "tests/contract",
        "tests/integration",
        "specs/001-statistical-cognitive-decline/contracts",
        "scripts"
    ]

    logger.info("Starting project directory structure creation...")
    success_count = 0
    fail_count = 0

    for dir_path in base_dirs:
        if create_directory(dir_path):
            success_count += 1
        else:
            fail_count += 1

    if fail_count == 0:
        logger.info(f"Successfully created all {success_count} directories.")
        sys.exit(0)
    else:
        logger.error(f"Failed to create {fail_count} directories. {success_count} succeeded.")
        sys.exit(1)

if __name__ == "__main__":
    main()