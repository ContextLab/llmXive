import os
import sys
import logging
from pathlib import Path
from typing import List
from config import get_logger, setup_logging

def ensure_data_directories(base_path: Path) -> List[Path]:
    """
    Ensure that the standard data directory structure exists.
    
    Creates the following directories relative to base_path:
    - data/raw
    - data/processed
    - data/results
    
    Uses robust mkdir -p logic (exist_ok=True) to avoid errors if
    directories already exist.
    
    Args:
        base_path: The root path where the 'data' directory should be created.
        
    Returns:
        A list of Path objects for the created/ensured directories.
        
    Raises:
        RuntimeError: If any directory creation fails unexpectedly.
    """
    logger = get_logger()
    
    data_dirs = [
        base_path / "data" / "raw",
        base_path / "data" / "processed",
        base_path / "data" / "results",
    ]
    
    created_dirs = []
    
    for dir_path in data_dirs:
        try:
            dir_path.mkdir(parents=True, exist_ok=True)
            created_dirs.append(dir_path)
            logger.info(f"Ensured directory exists: {dir_path}")
        except OSError as e:
            logger.error(f"Failed to create directory {dir_path}: {e}")
            raise RuntimeError(f"Failed to create directory {dir_path}: {e}") from e
    
    return created_dirs

def main() -> None:
    """
    Entry point for script execution.
    
    Ensures the data directory structure exists relative to the project root.
    Prints the paths of the ensured directories to stdout.
    """
    setup_logging()
    logger = get_logger()
    
    # Determine project root: assume script is at code/utils/directories.py
    # Project root is two levels up from this file.
    script_path = Path(__file__).resolve()
    project_root = script_path.parent.parent.parent
    
    logger.info(f"Project root detected at: {project_root}")
    
    try:
        ensured_dirs = ensure_data_directories(project_root)
        logger.info(f"Successfully ensured {len(ensured_dirs)} directories.")
        
        # Print paths to stdout for verification
        for d in ensured_dirs:
            print(str(d))
            
    except RuntimeError as e:
        logger.critical(f"Directory setup failed: {e}")
        sys.exit(1)

    logger.info("Directory structure verification complete.")

if __name__ == "__main__":
    main()