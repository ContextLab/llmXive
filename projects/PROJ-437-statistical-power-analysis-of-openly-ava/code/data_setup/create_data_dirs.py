"""
Directory creation utility for the llmXive statistical power analysis project.
This module creates the required data directory structure as specified in T001c.
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

def create_data_directories(root_dir: Path) -> None:
    """
    Create the required data directory structure.

    Creates:
    - data/
    - data/raw/
    - data/derived/
    - data/aggregated/

    Args:
        root_dir: The project root directory path.
    """
    data_base = root_dir / "data"
    
    directories = [
        data_base,
        data_base / "raw",
        data_base / "derived",
        data_base / "aggregated",
    ]

    created_count = 0
    for dir_path in directories:
        if not dir_path.exists():
            dir_path.mkdir(parents=True, exist_ok=True)
            logger.info(f"Created directory: {dir_path}")
            created_count += 1
        else:
            logger.info(f"Directory already exists: {dir_path}")

    logger.info(f"Data directory creation complete. {created_count} new directories created.")

def main() -> int:
    """
    Main entry point for the script.
    Creates data directories relative to the current working directory.
    
    Returns:
        0 on success, 1 on failure.
    """
    try:
        # Assume project root is the current working directory
        root_dir = Path.cwd()
        logger.info(f"Creating data directories in: {root_dir}")
        create_data_directories(root_dir)
        return 0
    except Exception as e:
        logger.error(f"Failed to create data directories: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
