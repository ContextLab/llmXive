import os
import sys
import logging
from pathlib import Path
from code.utils.logging import setup_logging, get_logger
from code.utils.directories import create_all_directories

logger = get_logger(__name__)

def main():
    """
    Main entry point to run the directory setup script.
    This script implements T001a.
    """
    setup_logging()
    logger.info("Running T001a: Initialize directory structure...")
    try:
        created_dirs = create_all_directories()
        logger.info(f"Successfully initialized {len(created_dirs)} directories.")
        for d in created_dirs:
            logger.info(f"  Created: {d}")
        return 0
    except Exception as e:
        logger.error(f"Failed to initialize directories: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())