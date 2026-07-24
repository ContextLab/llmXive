import os
import sys
from pathlib import Path
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def create_directories(base_path: Path) -> None:
    """
    Create the required source directory structure for the project.
    
    Specifically creates:
    - code/utils
    - code/data
    
    Args:
        base_path: The root directory of the project (projects/PROJ-096-exploring-the-role-of-network-topology-o)
    """
    directories = [
        base_path / "code" / "utils",
        base_path / "code" / "data",
    ]
    
    created_count = 0
    for dir_path in directories:
        if not dir_path.exists():
            dir_path.mkdir(parents=True, exist_ok=True)
            logger.info(f"Created directory: {dir_path}")
            created_count += 1
        else:
            logger.info(f"Directory already exists: {dir_path}")
    
    logger.info(f"Directory creation complete. {created_count} new directories created.")

def main() -> int:
    """
    Main entry point for the directory setup script.
    
    Returns:
        0 on success, 1 on failure.
    """
    # Determine the project root based on the task description
    # The task specifies: projects/PROJ-096-exploring-the-role-of-network-topology-o/
    # We assume the script is run from the repository root or we construct the path relative to script location
    script_dir = Path(__file__).resolve().parent
    repo_root = script_dir.parent.parent.parent # Assuming code/ is at repo_root/code/
    
    # Adjust for the specific project path mentioned in the task
    # If the script is inside projects/PROJ-.../code/, then parent.parent is the project root
    # Let's assume the standard structure where this script is at code/setup_directories.py
    # and the project root is the parent of the 'code' directory.
    project_root = script_dir.parent
    
    # Verify we are in the correct project context if possible, 
    # but for this task, we strictly follow the path relative to the script's assumed location
    # The task says: "in projects/PROJ-096-exploring-the-role-of-network-topology-o/"
    # If this file is at projects/PROJ-096.../code/setup_directories.py, then project_root is correct.
    
    logger.info(f"Project root identified as: {project_root}")
    
    try:
        create_directories(project_root)
        return 0
    except Exception as e:
        logger.error(f"Failed to create directories: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
