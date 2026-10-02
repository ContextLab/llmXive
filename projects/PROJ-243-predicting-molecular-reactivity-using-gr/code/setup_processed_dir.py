import os
import sys
import logging
from typing import Optional
from config import get_config, ensure_directories

def setup_script_logging():
    """Initialize logging for the setup_processed_dir script."""
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    return logger

def ensure_processed_directory(config: Optional[dict] = None) -> str:
    """
    Ensures the data/processed directory exists.
    
    Args:
        config: Optional configuration dictionary. If None, loads default config.
    
    Returns:
        The absolute path to the created/existing directory.
    
    Raises:
        RuntimeError: If the directory cannot be created.
    """
    logger = logging.getLogger(__name__)
    if config is None:
        config = get_config()
    
    processed_dir = config.get('paths', {}).get('processed', 'data/processed')
    
    # Ensure parent directories exist
    parent_dir = os.path.dirname(processed_dir)
    if parent_dir and not os.path.exists(parent_dir):
        os.makedirs(parent_dir, exist_ok=True)
        logger.info(f"Created parent directory: {parent_dir}")
    
    try:
        os.makedirs(processed_dir, exist_ok=True)
        logger.info(f"Successfully ensured existence of: {processed_dir}")
        return os.path.abspath(processed_dir)
    except OSError as e:
        logger.error(f"Failed to create directory {processed_dir}: {e}")
        raise RuntimeError(f"Failed to create directory {processed_dir}") from e

def main():
    """Main entry point for ensuring the processed data directory exists."""
    logger = setup_script_logging()
    logger.info("Starting directory setup for data/processed")
    
    try:
        config = get_config()
        path = ensure_processed_directory(config)
        logger.info(f"Task T001b completed: Directory '{path}' is ready.")
        return 0
    except Exception as e:
        logger.error(f"Task T001b failed: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
