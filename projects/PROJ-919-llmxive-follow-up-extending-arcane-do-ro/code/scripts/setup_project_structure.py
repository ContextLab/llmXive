import os
import sys
from pathlib import Path
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Define the required directory structure relative to the project root
# Based on tasks.md: T001 requires specific paths under the project root
DIRECTORIES = [
    "src",
    "tests",
    "data",
    "data/raw",
    "data/derived",
    "data/gold_standard",
    "artifacts",
    "specs/001-llmxive-follow-up-extending-arcane-do-ro"
]

# Project root is the parent of the 'code' directory (assuming this script is in code/scripts/)
# However, per constraints, paths are relative to project root.
# We assume the script is run from the project root or we calculate it.
# To be safe and robust, we determine the root based on the presence of 'specs' or 'src' if they exist,
# or assume current working directory is the root.
# Given the task is to CREATE the structure, we assume we are running from the root.

PROJECT_ROOT = Path.cwd()

def setup_directories():
    """
    Creates the required project directory structure.
    Logs the creation of each directory.
    """
    logger.info(f"Setting up project structure in: {PROJECT_ROOT}")
    
    created_count = 0
    skipped_count = 0

    for dir_path in DIRECTORIES:
        full_path = PROJECT_ROOT / dir_path
        
        if full_path.exists():
            logger.debug(f"Directory already exists: {full_path}")
            skipped_count += 1
            continue
        
        try:
            full_path.mkdir(parents=True, exist_ok=True)
            logger.info(f"Created directory: {full_path}")
            created_count += 1
        except OSError as e:
            logger.error(f"Failed to create directory {full_path}: {e}")
            raise

    logger.info(f"Directory setup complete. Created: {created_count}, Skipped: {skipped_count}")
    return True

def main():
    """
    Entry point for the script.
    """
    try:
        setup_directories()
        logger.info("Project structure initialization successful.")
        return 0
    except Exception as e:
        logger.error(f"Project structure initialization failed: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
