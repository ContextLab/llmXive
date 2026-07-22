import os
import sys
from pathlib import Path
from utils.logging import get_logger

# Define the project root relative to this script location
# Assuming this script is at code/setup_directories.py
# We need to go up one level to reach the project root
PROJECT_ROOT = Path(__file__).parent.parent

def main():
    """
    Creates the required directories for the llmXive project:
    - data/
    - state/
    - docs/
    
    This implements task T001d.
    """
    logger = get_logger("setup_directories")
    
    directories_to_create = [
        "data",
        "state",
        "docs"
    ]
    
    created_paths = []
    
    for dir_name in directories_to_create:
        target_path = PROJECT_ROOT / dir_name
        
        if not target_path.exists():
            try:
                target_path.mkdir(parents=True, exist_ok=True)
                logger.info(f"Created directory: {target_path}")
                created_paths.append(str(target_path))
            except OSError as e:
                logger.error(f"Failed to create directory {target_path}: {e}")
                raise
        else:
            logger.info(f"Directory already exists: {target_path}")
            created_paths.append(str(target_path))
    
    logger.info(f"Setup complete. Created/Verified directories: {created_paths}")
    return created_paths

if __name__ == "__main__":
    main()
