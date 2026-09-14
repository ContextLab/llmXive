import os
import sys
from typing import List

from utils.logging import get_logger, log_info, log_error

logger = get_logger(__name__)

def create_directories() -> List[str]:
    """
    Create the required data directory structure for the project.
    
    Directories created:
    - data/raw
    - data/processed
    - data/artifacts
    
    Returns:
        List[str]: List of created directory paths.
    """
    base_dir = "data"
    directories = [
        os.path.join(base_dir, "raw"),
        os.path.join(base_dir, "processed"),
        os.path.join(base_dir, "artifacts"),
    ]
    
    created = []
    for dir_path in directories:
        if not os.path.exists(dir_path):
            try:
                os.makedirs(dir_path, exist_ok=True)
                log_info(logger, f"Created directory: {dir_path}")
                created.append(dir_path)
            except OSError as e:
                log_error(logger, f"Failed to create directory {dir_path}: {e}")
                raise
        else:
            log_info(logger, f"Directory already exists: {dir_path}")
            created.append(dir_path)
    
    return created

def main() -> int:
    """
    Entry point for the data directory setup script.
    
    Returns:
        int: Exit code (0 for success, 1 for failure).
    """
    try:
        log_info(logger, "Starting data directory setup...")
        created_dirs = create_directories()
        log_info(logger, f"Successfully created/verified {len(created_dirs)} directories.")
        return 0
    except Exception as e:
        log_error(logger, f"Data directory setup failed: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
