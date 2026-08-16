import os
import sys
from pathlib import Path
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def ensure_directory(path: Path) -> bool:
    """
    Ensures that the specified directory exists.
    Creates it if it does not exist.
    
    Args:
        path (Path): The directory path to ensure exists.
        
    Returns:
        bool: True if the directory exists or was created successfully, False otherwise.
    """
    try:
        path.mkdir(parents=True, exist_ok=True)
        logger.info(f"Directory ensured: {path}")
        return True
    except OSError as e:
        logger.error(f"Failed to create directory {path}: {e}")
        return False

def main():
    """
    Main function to create the required data directories for the project.
    """
    # Define the project root relative to this script's location or current working directory
    # Assuming the script is run from the project root or the path is relative to cwd
    project_root = Path.cwd()
    
    # Define the specific directories required by T001a
    # Path: projects/PROJ-967-llmxive-follow-up-extending-beyond-scala/
    # Since the task asks for paths relative to the repository root, and we are likely
    # in the repo root, we construct the full path.
    base_path = project_root / "projects" / "PROJ-967-llmxive-follow-up-extending-beyond-scala"
    
    directories_to_create = [
        base_path / "data" / "raw",
        base_path / "data" / "processed",
        base_path / "results"
    ]
    
    logger.info(f"Starting directory creation for project: {base_path}")
    
    all_success = True
    for dir_path in directories_to_create:
        if not ensure_directory(dir_path):
            all_success = False
            logger.warning(f"Skipping subsequent directories due to failure at {dir_path}")
            # Depending on strictness, we might break here. 
            # The task requires creating these specific dirs.
            break
    
    if all_success:
        logger.info("All required directories created successfully.")
    else:
        logger.error("Some directories failed to be created.")
        sys.exit(1)

if __name__ == "__main__":
    main()
