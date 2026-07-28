"""
Script to create the required data directory structure for the project.
This implements task T001b.
"""
import os
import sys
import logging
from pathlib import Path
from utils.logging import get_logger
from utils.config import get_project_root

# Define the data directory structure to create
DATA_DIRS = [
    "data/raw",
    "data/processed",
    "data/splits",
    "data/schemas"
]

def create_data_directories(project_root: Path) -> bool:
    """
    Create the required data directory structure.
    
    Args:
        project_root: Path to the project root directory
        
    Returns:
        bool: True if all directories were created successfully, False otherwise
    """
    logger = get_logger("setup_data")
    success = True
    
    for dir_path in DATA_DIRS:
        full_path = project_root / dir_path
        try:
            full_path.mkdir(parents=True, exist_ok=True)
            logger.info(f"Created directory: {full_path}")
        except OSError as e:
            logger.error(f"Failed to create directory {full_path}: {e}")
            success = False
            
    return success

def main():
    """Main entry point for the data directory setup script."""
    logger = get_logger("setup_data")
    logger.info("Starting data directory structure creation...")
    
    project_root = get_project_root()
    logger.info(f"Project root: {project_root}")
    
    if create_data_directories(project_root):
        logger.info("Data directory structure created successfully.")
        # List the created directories
        data_dir = project_root / "data"
        if data_dir.exists():
            logger.info("Created directories:")
            for item in sorted(data_dir.rglob("*")):
                if item.is_dir():
                    rel_path = item.relative_to(project_root)
                    logger.info(f"  {rel_path}")
        return 0
    else:
        logger.error("Failed to create some data directories.")
        return 1

if __name__ == "__main__":
    sys.exit(main())