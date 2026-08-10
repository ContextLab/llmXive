import os
import sys
import logging
from utils import get_logger, set_task_id, get_task_id

# Constants for data directories relative to project root
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(PROJECT_ROOT, "data")
RAW_DIR = os.path.join(DATA_DIR, "raw")
GENERATED_DIR = os.path.join(DATA_DIR, "generated")
ANALYSIS_DIR = os.path.join(DATA_DIR, "analysis")

def create_directories():
    """
    Creates the required data directory structure:
    - data/raw/
    - data/generated/
    - data/analysis/

    Constraint: Does NOT create 'state/' as that is handled in T001a at the root level.
    """
    logger = get_logger()
    logger.info("Starting T008: Creating data directory structure")

    directories = [RAW_DIR, GENERATED_DIR, ANALYSIS_DIR]

    for directory in directories:
        if not os.path.exists(directory):
            os.makedirs(directory)
            logger.info(f"Created directory: {directory}")
        else:
            logger.info(f"Directory already exists: {directory}")

    logger.info("T008 completed: Data directory structure created successfully")
    return True

def main():
    """Main entry point for T008."""
    set_task_id("T008")
    logger = get_logger()
    logger.info("Starting T008 data directory creation")

    try:
        create_directories()
        logger.info("T008 SUCCESS: Data directories created")
        return 0
    except Exception as e:
        logger.error(f"T008 FAILED: {str(e)}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
