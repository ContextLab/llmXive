"""
Script to create and initialize the data/assets directory.
This directory will store canonical, verified data files ready for model training.
"""
import os
import sys
import logging
from typing import Optional

# Import from existing project API
from config import get_config, ensure_directories

def setup_script_logging() -> logging.Logger:
    """Configure logging for the setup script."""
    logger = logging.getLogger("setup_assets_dir")
    logger.setLevel(logging.INFO)
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    return logger

def create_assets_directory(config: Optional[dict] = None) -> str:
    """
    Create the data/assets directory if it does not exist.
    
    Args:
        config: Optional configuration dictionary. If None, loads from config.py.
        
    Returns:
        The absolute path to the created directory.
        
    Raises:
        OSError: If the directory cannot be created.
    """
    logger = setup_script_logging()
    
    if config is None:
        config = get_config()
    
    # Ensure the base data directory exists first
    data_dir = config.get("data_dir", "data")
    ensure_directories(config)
    
    assets_dir = os.path.join(data_dir, "assets")
    
    logger.info(f"Ensuring existence of assets directory: {assets_dir}")
    
    try:
        os.makedirs(assets_dir, exist_ok=True)
        logger.info(f"Assets directory ready: {assets_dir}")
        return assets_dir
    except OSError as e:
        logger.error(f"Failed to create assets directory {assets_dir}: {e}")
        raise

def main() -> int:
    """
    Main entry point for the script.
    
    Returns:
        0 on success, 1 on failure.
    """
    logger = setup_script_logging()
    try:
        create_assets_directory()
        logger.info("Task T001c completed successfully: data/assets directory created.")
        return 0
    except Exception as e:
        logger.error(f"Task T001c failed: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
