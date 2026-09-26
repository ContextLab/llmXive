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

def create_directory(path: str) -> bool:
    """
    Create a directory if it does not exist.
    
    Args:
        path: The path to the directory to create.
        
    Returns:
        True if the directory was created or already exists, False otherwise.
    """
    try:
        dir_path = Path(path)
        dir_path.mkdir(parents=True, exist_ok=True)
        logger.info(f"Directory created/verified: {dir_path}")
        return True
    except Exception as e:
        logger.error(f"Failed to create directory {path}: {e}")
        return False

def main():
    """
    Main function to create the project directory structure.
    """
    # Define the required directories
    directories = [
        "data/raw",
        "data/interim",
        "data/results",
        "data/processed",
        "code",
        "tests/unit",
        "tests/contract",
        "tests/integration",
        "specs/001-statistical-cognitive-decline/contracts"
    ]

    logger.info("Starting directory structure creation...")
    success = True

    for dir_path in directories:
        if not create_directory(dir_path):
            success = False

    if success:
        logger.info("Directory structure created successfully.")
        print("SUCCESS: Directory structure created.")
        sys.exit(0)
    else:
        logger.error("Failed to create some directories.")
        print("FAILURE: Some directories could not be created.")
        sys.exit(1)

if __name__ == "__main__":
    main()