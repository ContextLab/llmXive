import os
import sys
from pathlib import Path
from utils.logging import get_logger

logger = get_logger(__name__)

def create_directory(dir_path: str) -> bool:
    """
    Create a directory if it does not exist.
    
    Args:
        dir_path: The path to the directory to create.
        
    Returns:
        True if the directory was created or already exists, False otherwise.
    """
    path = Path(dir_path)
    try:
        if not path.exists():
            path.mkdir(parents=True, exist_ok=True)
            logger.info(f"Created directory: {path.resolve()}")
            return True
        else:
            logger.info(f"Directory already exists: {path.resolve()}")
            return True
    except Exception as e:
        logger.error(f"Failed to create directory {path}: {e}")
        return False

def main():
    """
    Main function to create the required project directories:
    data/, state/, and docs/.
    """
    # Define the directories to create relative to the project root
    # Assuming the script is run from the project root or code/ directory
    # We use the parent of the script location as the project root if running from code/
    script_dir = Path(__file__).parent.resolve()
    project_root = script_dir.parent if script_dir.name == "code" else script_dir
    
    directories = [
        project_root / "data",
        project_root / "state",
        project_root / "docs"
    ]
    
    logger.info(f"Project root identified as: {project_root}")
    logger.info("Creating required directories: data/, state/, docs/")
    
    all_success = True
    for directory in directories:
        if not create_directory(str(directory)):
            all_success = False
    
    if all_success:
        logger.info("All directories created successfully.")
        return 0
    else:
        logger.error("Some directories failed to create.")
        return 1

if __name__ == "__main__":
    sys.exit(main())