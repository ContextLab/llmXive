import os
import sys
from typing import List

from utils.logging import get_logger, log_info, log_error

logger = get_logger(__name__)

def create_directories() -> bool:
    """
    Create the project state directory structure.
    
    Specifically creates 'state/' and 'state/PROJ-485/' to satisfy
    Constitution Principle V (State Management) and Task T001c.
    
    Returns:
        bool: True if successful, False otherwise.
    """
    base_dir = "state"
    project_dir = os.path.join(base_dir, "PROJ-485")
    
    directories_to_create = [base_dir, project_dir]
    
    created_count = 0
    failed_count = 0
    
    for dir_path in directories_to_create:
        try:
            if not os.path.exists(dir_path):
                os.makedirs(dir_path, exist_ok=True)
                log_info(logger, f"Created directory: {dir_path}")
                created_count += 1
            else:
                log_info(logger, f"Directory already exists: {dir_path}")
        except OSError as e:
            log_error(logger, f"Failed to create directory {dir_path}: {e}")
            failed_count += 1
    
    if failed_count > 0:
        log_error(logger, f"Failed to create {failed_count} directory(ies)")
        return False
        
    log_info(logger, f"Successfully created {created_count} state directories")
    return True

def main():
    """Entry point for script execution."""
    logger.info("Starting state directory creation (Task T001c)")
    success = create_directories()
    if success:
        logger.info("State directory creation completed successfully")
        sys.exit(0)
    else:
        logger.error("State directory creation failed")
        sys.exit(1)

if __name__ == "__main__":
    main()
