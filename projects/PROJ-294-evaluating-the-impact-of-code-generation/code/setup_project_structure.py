"""
T001a: Create directory structure for the project.
Creates code/, data/, results/, tests/, docs/ under the project root.
Creates .gitkeep files in each directory to ensure they are tracked by git.
"""
import os
import sys
import logging
from datetime import datetime
from utils import setup_logging, get_logger, set_task_id, get_unique_id

# Ensure the logging infrastructure is set up before defining the function
# This handles cases where this script is run standalone or imported
if not logging.getLogger().handlers:
    setup_logging()

TASK_ID = "T001a"
set_task_id(TASK_ID)
logger = get_logger()

def ensure_directory(path: str) -> bool:
    """
    Ensure a directory exists. Create it if it doesn't.
    Returns True if successful, False otherwise.
    """
    try:
        os.makedirs(path, exist_ok=True)
        logger.info(f"Directory ensured: {path}")
        return True
    except Exception as e:
        logger.error(f"Failed to create directory {path}: {e}")
        return False

def create_init_file(path: str) -> bool:
    """
    Create a .gitkeep file in the specified directory to ensure git tracks it.
    Returns True if successful, False otherwise.
    """
    try:
        gitkeep_path = os.path.join(path, ".gitkeep")
        with open(gitkeep_path, 'w') as f:
            f.write("# Git keep file to track directory\n")
        logger.info(f"Created .gitkeep file: {gitkeep_path}")
        return True
    except Exception as e:
        logger.error(f"Failed to create .gitkeep file in {path}: {e}")
        return False

def main():
    """
    Main function to create the project directory structure.
    """
    logger.info(f"Starting task {TASK_ID}: Create directory structure")
    
    # Define the project root based on the task description
    # The task specifies: projects/PROJ-294-evaluating-the-impact-of-code-generation/
    # We assume the script is run from the repository root
    project_root = "projects/PROJ-294-evaluating-the-impact-of-code-generation"
    
    # Ensure the parent project directory exists first
    if not ensure_directory(project_root):
        logger.error(f"Failed to create project root: {project_root}")
        return 1

    # Define the subdirectories to create
    subdirectories = ["code", "data", "results", "tests", "docs"]
    
    success = True
    for subdir in subdirectories:
        full_path = os.path.join(project_root, subdir)
        if not ensure_directory(full_path):
            success = False
        elif not create_init_file(full_path):
            success = False
    
    if success:
        logger.info(f"Task {TASK_ID} completed successfully. Directory structure created.")
        # Verify existence as per task constraint
        for subdir in subdirectories:
            full_path = os.path.join(project_root, subdir)
            if os.path.isdir(full_path):
                logger.info(f"Verified: {full_path} exists")
            else:
                logger.error(f"Verification failed: {full_path} does not exist")
                success = False
    else:
        logger.error(f"Task {TASK_ID} failed with errors.")
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())