import os
import sys
from pathlib import Path
import logging

from utils.logging import get_logger

logger = get_logger(__name__)


def setup_data_directories(base_path: str = "data") -> bool:
    """
    Create the main data directory and its subdirectories (raw, processed, interim).
    
    Args:
        base_path: Relative path to the data directory.
        
    Returns:
        True if all directories exist after the operation, False otherwise.
    """
    data_path = Path(base_path)
    subdirs = ["raw", "processed", "interim"]
    
    # Ensure base data directory exists
    if not data_path.exists():
        try:
            data_path.mkdir(parents=True, exist_ok=True)
            logger.info(f"Created data directory: {data_path.absolute()}")
        except OSError as e:
            logger.error(f"Failed to create data directory: {e}")
            return False
    
    # Ensure subdirectories exist
    for subdir in subdirs:
        subdir_path = data_path / subdir
        if not subdir_path.exists():
            try:
                subdir_path.mkdir(parents=True, exist_ok=True)
                logger.info(f"Created subdirectory: {subdir_path.absolute()}")
            except OSError as e:
                logger.error(f"Failed to create subdirectory {subdir}: {e}")
                return False
                
        # Create .gitkeep to ensure directory is tracked by git
        gitkeep_path = subdir_path / ".gitkeep"
        if not gitkeep_path.exists():
            try:
                gitkeep_path.touch()
                logger.debug(f"Created .gitkeep in {subdir_path.absolute()}")
            except OSError as e:
                logger.warning(f"Failed to create .gitkeep in {subdir}: {e}")
    
    return True


def main() -> int:
    """
    Main entry point for the script.
    
    Returns:
        0 on success, 1 on failure.
    """
    success = setup_data_directories()
    
    if not success:
        logger.error("Setup failed: Some data directories could not be created.")
        return 1
        
    logger.info("Setup completed: All data directories are ready.")
    return 0


if __name__ == "__main__":
    sys.exit(main())