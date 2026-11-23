"""
Script to create and ensure the existence of the 'data/processed' directory.
This task corresponds to T001b in the project plan.
"""
import os
import sys
import logging
from typing import Optional

from config import get_config, ensure_directories


def setup_script_logging() -> logging.Logger:
    """
    Sets up logging for this script.
    Returns a logger instance.
    """
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    return logger


def ensure_processed_directory(config: Optional[dict] = None) -> str:
    """
    Ensures the 'data/processed' directory exists.
    If it does not exist, it creates it.
    Returns the path to the directory.
    
    Args:
        config: Optional configuration dictionary. If None, loads from get_config().
        
    Returns:
        str: Absolute path to the data/processed directory.
        
    Raises:
        OSError: If the directory cannot be created.
    """
    logger = setup_script_logging()
    
    if config is None:
        config = get_config()
        
    # Get the base data directory from config
    base_data_dir = config.get('data', {}).get('base_dir', 'data')
    processed_dir = os.path.join(base_data_dir, 'processed')
    
    logger.info(f"Ensuring directory exists: {processed_dir}")
    
    try:
        os.makedirs(processed_dir, exist_ok=True)
        logger.info(f"Directory '{processed_dir}' is ready.")
        return os.path.abspath(processed_dir)
    except OSError as e:
        logger.error(f"Failed to create directory '{processed_dir}': {e}")
        raise


def main() -> int:
    """
    Main entry point for the script.
    Returns 0 on success, 1 on failure.
    """
    logger = setup_script_logging()
    try:
        path = ensure_processed_directory()
        logger.info(f"Successfully ensured 'data/processed' directory at: {path}")
        return 0
    except Exception as e:
        logger.error(f"Script failed: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())