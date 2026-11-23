import os
import sys
from typing import List
from utils.logging import get_logger, log_info, log_error

logger = get_logger(__name__)

def create_directories() -> None:
    """
    Create the project state directory structure.
    
    Creates:
        - state/
        - state/PROJ-485/
        
    This implements Task T001c: Create project directory structure: `state/`.
    """
    base_dirs = [
        "state",
        "state/PROJ-485"
    ]
    
    created_count = 0
    for dir_path in base_dirs:
        if not os.path.exists(dir_path):
            try:
                os.makedirs(dir_path, exist_ok=True)
                log_info(logger, f"Created directory: {dir_path}")
                created_count += 1
            except OSError as e:
                log_error(logger, f"Failed to create directory {dir_path}: {e}")
                raise
        else:
            log_info(logger, f"Directory already exists: {dir_path}")
    
    log_info(logger, f"State directory setup complete. Created {created_count} new directories.")

def main() -> None:
    """Entry point for directory creation script."""
    log_info(logger, "Starting state directory creation...")
    create_directories()
    log_info(logger, "State directory creation finished.")

if __name__ == "__main__":
    main()
