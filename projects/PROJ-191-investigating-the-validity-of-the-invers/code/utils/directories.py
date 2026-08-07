import os
import sys
import logging
from pathlib import Path
from typing import List
from config import get_logger, setup_logging

def ensure_data_directories(base_path: Path) -> List[Path]:
    """
    Ensure that the required data directory structure exists.
    Uses robust mkdir -p logic (exist_ok=True) to create directories
    if they do not exist, and does not fail if they already exist.

    Args:
        base_path: The root path where data directories should be created.
                   Typically the project root or a specific data root.

    Returns:
        A list of Path objects for the directories that were ensured.
    """
    logger = get_logger()
    directories = [
        base_path / "data" / "raw",
        base_path / "data" / "processed",
        base_path / "data" / "results",
    ]

    created_or_existing = []
    for dir_path in directories:
        try:
            dir_path.mkdir(parents=True, exist_ok=True)
            created_or_existing.append(dir_path)
            logger.info(f"Ensured directory: {dir_path}")
        except PermissionError as e:
            logger.error(f"Permission denied creating directory {dir_path}: {e}")
            raise
        except OSError as e:
            logger.error(f"Error creating directory {dir_path}: {e}")
            raise

    return created_or_existing

def main():
    """
    Entry point for ensuring data directories when run as a script.
    Assumes the script is run from the project root or code/ directory.
    """
    setup_logging()
    logger = get_logger()
    
    # Determine project root. 
    # If run as `python code/utils/directories.py`, cwd is likely project root.
    # If run as `python -m code.utils.directories`, we need to handle module path.
    # We assume the project root is the parent of the 'code' directory.
    current_file = Path(__file__).resolve()
    code_dir = current_file.parent
    project_root = code_dir.parent
    
    logger.info(f"Project root detected at: {project_root}")
    
    try:
        dirs = ensure_data_directories(project_root)
        logger.info(f"Successfully ensured {len(dirs)} directories.")
        for d in dirs:
            print(f"OK: {d}")
    except Exception as e:
        logger.critical(f"Failed to ensure directories: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()