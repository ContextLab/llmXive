import os
import sys
from typing import List

from utils.logging import get_logger, log_info, log_error

logger = get_logger(__name__)

def create_directories(project_id: str = "PROJ-485") -> List[str]:
    """
    Creates the project state directory structure.
    
    Args:
        project_id: The specific project identifier (default: PROJ-485).
        
    Returns:
        List[str]: Absolute paths of created directories.
    """
    base_state_dir = "state"
    project_state_dir = os.path.join(base_state_dir, project_id)
    
    created_dirs = []
    
    try:
        # Create the base state directory if it doesn't exist
        if not os.path.exists(base_state_dir):
            os.makedirs(base_state_dir)
            log_info(logger, f"Created base state directory: {base_state_dir}")
        else:
            log_info(logger, f"Base state directory already exists: {base_state_dir}")
        
        # Create the project-specific state directory
        if not os.path.exists(project_state_dir):
            os.makedirs(project_state_dir)
            log_info(logger, f"Created project state directory: {project_state_dir}")
            created_dirs.append(project_state_dir)
        else:
            log_info(logger, f"Project state directory already exists: {project_state_dir}")
            
    except OSError as e:
        log_error(logger, f"Failed to create state directories: {e}")
        raise
        
    return created_dirs

def main():
    """
    Entry point for creating state directories.
    """
    logger.info("Starting state directory creation...")
    try:
        dirs = create_directories()
        logger.info(f"Successfully created directories: {dirs}")
        return 0
    except Exception as e:
        logger.error(f"Failed to create state directories: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
