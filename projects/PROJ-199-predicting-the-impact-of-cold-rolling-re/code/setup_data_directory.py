import os
import sys
from pathlib import Path
import logging
from utils.logging import get_logger

def ensure_data_directory(base_path: Optional[Path] = None) -> Path:
    """
    Creates the 'data' directory at the project root if it does not exist.
    
    Args:
        base_path: Optional base path. If None, uses the directory of this module.
        
    Returns:
        The Path object for the created or existing 'data' directory.
        
    Raises:
        OSError: If the directory cannot be created due to permissions or other OS errors.
    """
    if base_path is None:
        # Default to the directory containing this script (code/)
        # The project root is the parent of 'code'
        base_path = Path(__file__).resolve().parent.parent
    
    data_dir = base_path.joinpath('data')
    
    logger = get_logger(__name__)
    
    if not data_dir.is_dir():
        logger.info(f"Creating data directory: {data_dir}")
        try:
            data_dir.mkdir(parents=True, exist_ok=True)
            # Create a .gitkeep file to ensure the directory is tracked by git
            gitkeep_path = data_dir.joinpath('.gitkeep')
            if not gitkeep_path.exists():
                gitkeep_path.touch()
                logger.debug(f"Created .gitkeep in {data_dir}")
        except OSError as e:
            logger.error(f"Failed to create data directory {data_dir}: {e}")
            raise
    else:
        logger.debug(f"Data directory already exists: {data_dir}")
        
    return data_dir

def verify_data_directory(base_path: Optional[Path] = None) -> bool:
    """
    Verifies that the 'data' directory exists using pathlib.
    
    This function implements the specific verification requirement:
    `pathlib.Path(__file__).parent.joinpath('data').is_dir()`
    
    Args:
        base_path: Optional base path. If None, uses the directory of this module.
        
    Returns:
        True if the directory exists, False otherwise.
    """
    if base_path is None:
        base_path = Path(__file__).resolve().parent.parent
        
    data_dir = base_path.joinpath('data')
    exists = data_dir.is_dir()
    
    logger = get_logger(__name__)
    if exists:
        logger.debug(f"Verification passed: {data_dir} exists.")
    else:
        logger.warning(f"Verification failed: {data_dir} does not exist.")
        
    return exists

def main():
    """
    Main entry point for the script.
    Creates the data directory and verifies its existence.
    """
    logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
    logger = get_logger(__name__)
    
    try:
        data_dir = ensure_data_directory()
        if verify_data_directory():
            logger.info(f"Successfully ensured data directory exists at: {data_dir}")
            return 0
        else:
            logger.error("Verification failed after creation attempt.")
            return 1
    except OSError as e:
        logger.error(f"Critical error during setup: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
