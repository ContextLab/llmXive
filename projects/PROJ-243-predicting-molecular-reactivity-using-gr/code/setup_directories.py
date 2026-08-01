import os
import sys
import logging
from config import ensure_directories

def setup_script_logging():
    """Initialize logging for the setup script."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )
    return logging.getLogger(__name__)

def main():
    """Create code, artifacts, and tests directories."""
    logger = setup_script_logging()
    logger.info("Starting directory setup for T001b...")
    
    # Define the directories required by T001b
    # Note: ensure_directories handles the creation of all required paths
    # including data/ subdirs (T001a) and these new ones.
    # We call it here to ensure the specific T001b targets are created.
    
    config_dirs = [
        'code',
        'artifacts',
        'tests'
    ]
    
    # ensure_directories is expected to take a list of relative paths or
    # use the config to determine them. Based on the API surface, 
    # ensure_directories is in config.py.
    # We will call it to ensure these specific directories exist.
    
    try:
        ensure_directories(config_dirs)
        logger.info("Successfully created directories: code, artifacts, tests")
    except Exception as e:
        logger.error(f"Failed to create directories: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()