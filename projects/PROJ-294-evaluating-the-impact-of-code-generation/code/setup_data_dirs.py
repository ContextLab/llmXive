import os
import sys
import logging
from utils import setup_logging, get_logger, set_task_id, get_task_id

def create_directories():
    """
    T008: Create data directory structure: data/raw/, data/generated/, data/analysis/
    """
    logger = setup_logging(task_id="T008")
    logger.info("Creating data directory structure...")

    base_data_dir = "data"
    sub_dirs = ["raw", "generated", "analysis"]

    for subdir in sub_dirs:
        full_path = os.path.join(base_data_dir, subdir)
        try:
            os.makedirs(full_path, exist_ok=True)
            logger.info(f"Created directory: {full_path}")
        except OSError as e:
            logger.error(f"Failed to create directory {full_path}: {e}")
            raise

def main():
    create_directories()

if __name__ == "__main__":
    main()
