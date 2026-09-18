"""
Script to create required project directories: code, artifacts, tests.
This task (T002) ensures the project structure is ready for implementation.
"""
import os
import sys
import logging
from typing import List
from config import ensure_directories, get_config

def setup_script_logging():
    """Configure logging for the setup script."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )
    return logging.getLogger(__name__)

def create_directories(logger: logging.Logger) -> List[str]:
    """
    Create the required project directories.
    
    Returns:
        List[str]: List of created directory paths.
    """
    config = get_config()
    # Define directories relative to project root
    required_dirs = [
        'code',
        'artifacts',
        'tests'
    ]
    
    created = []
    for dir_name in required_dirs:
        full_path = os.path.join(config['project_root'], dir_name)
        if not os.path.exists(full_path):
            os.makedirs(full_path, exist_ok=True)
            logger.info(f"Created directory: {full_path}")
            created.append(full_path)
        else:
            logger.info(f"Directory already exists: {full_path}")
            created.append(full_path)
    
    return created

def main():
    """Main entry point for directory setup."""
    logger = setup_script_logging()
    logger.info("Starting directory setup (Task T002)...")
    
    try:
        created_dirs = create_directories(logger)
        logger.info(f"Successfully created/verified {len(created_dirs)} directories.")
        logger.info("Directories ready: code, artifacts, tests")
    except Exception as e:
        logger.error(f"Failed to create directories: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
