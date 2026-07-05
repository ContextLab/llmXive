"""
Directory structure setup for the llmXive research pipeline.

This module creates the necessary directory structure for the project,
specifically the data subdirectories required for raw, processed, and results data.
"""
import os
from pathlib import Path
from typing import List

# Import the logger from the existing utils module
from utils.logging import get_logger

logger = get_logger(__name__)

def create_directories(base_path: Path) -> None:
    """
    Create the required directory structure for the project.
    
    This function creates the standard data subdirectories:
    - data/raw: For raw, unprocessed data
    - data/processed: For preprocessed data
    - data/results: For analysis results and reports
    
    Args:
        base_path: The root path of the project where directories should be created.
    """
    # Define the directory structure to create
    directories: List[Path] = [
        base_path / "data" / "raw",
        base_path / "data" / "processed",
        base_path / "data" / "results",
    ]

    created_count = 0
    for dir_path in directories:
        if not dir_path.exists():
            dir_path.mkdir(parents=True, exist_ok=True)
            logger.info(f"Created directory: {dir_path}")
            created_count += 1
        else:
            logger.debug(f"Directory already exists: {dir_path}")

    logger.info(f"Directory setup complete. Created {created_count} new directories.")

    # Verify all directories exist
    for dir_path in directories:
        if not dir_path.is_dir():
            raise RuntimeError(f"Failed to create required directory: {dir_path}")

def ensure_data_structure(project_root: Path) -> None:
    """
    Ensure the full data directory structure exists.
    
    This is a convenience wrapper that creates the directories if they don't exist.
    
    Args:
        project_root: The root path of the project.
    """
    create_directories(project_root)

if __name__ == "__main__":
    # When run directly, create directories in the current working directory's parent
    # or use a specified path from command line
    import sys

    if len(sys.argv) > 1:
        root = Path(sys.argv[1])
    else:
        # Default to the project root (parent of code/)
        root = Path(__file__).resolve().parent.parent

    print(f"Creating data directories at: {root}")
    ensure_data_structure(root)
    print("Done.")
