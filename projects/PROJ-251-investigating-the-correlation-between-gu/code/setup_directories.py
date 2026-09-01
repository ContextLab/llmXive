"""
Script to create the required project directory structure.
Ensures all necessary folders for data, code, tests, and research exist.
"""
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

# Define the root directory (project root)
ROOT_DIR = Path(__file__).resolve().parent.parent

# Define the directories to create relative to the root
DIRECTORIES = [
    "code",
    "data/raw",
    "data/processed",
    "data/results",
    "tests",
    "data/research"
]

def create_directories():
    """Create all required directories if they do not exist."""
    created_count = 0
    for dir_name in DIRECTORIES:
        target_path = ROOT_DIR / dir_name
        if not target_path.exists():
            target_path.mkdir(parents=True, exist_ok=True)
            logger.info(f"Created directory: {target_path}")
            created_count += 1
        else:
            logger.debug(f"Directory already exists: {target_path}")
    
    logger.info(f"Directory creation complete. Created {created_count} new directories.")
    return created_count

def main():
    """Main entry point for the script."""
    try:
        count = create_directories()
        logger.info("Success: All directories verified or created.")
        return 0
    except Exception as e:
        logger.error(f"Failed to create directories: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
