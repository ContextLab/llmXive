import os
import sys
from pathlib import Path
from utils.logger import get_logger

def create_directories(root_path: Path) -> None:
    """
    Initialize the project directory structure.
    
    Creates the following directories relative to root_path:
    - code/
    - tests/
    - data/ (including subdirectories: raw, processed, derived, config, logs)
    - docs/
    
    Args:
        root_path: The project root directory path.
    """
    logger = get_logger(__name__)
    
    # Define the directories to create
    directories = [
        "code",
        "tests",
        "docs",
        "data/raw",
        "data/processed",
        "data/derived",
        "data/config",
        "data/logs",
        "figures"
    ]
    
    for dir_name in directories:
        dir_path = root_path / dir_name
        try:
            dir_path.mkdir(parents=True, exist_ok=True)
            logger.info(f"Directory created: {dir_path}")
        except OSError as e:
            logger.error(f"Failed to create directory {dir_path}: {e}")
            raise

def verify_structure(root_path: Path) -> bool:
    """
    Verify that the required directory structure exists.
    
    Args:
        root_path: The project root directory path.
        
    Returns:
        True if all required directories exist, False otherwise.
    """
    required_dirs = [
        "code",
        "tests",
        "docs",
        "data/raw",
        "data/processed",
        "data/derived",
        "data/config",
        "data/logs",
        "figures"
    ]
    
    missing_dirs = []
    for dir_name in required_dirs:
        dir_path = root_path / dir_name
        if not dir_path.exists() or not dir_path.is_dir():
            missing_dirs.append(dir_name)
    
    if missing_dirs:
        logger = get_logger(__name__)
        logger.warning(f"Missing directories: {missing_dirs}")
        return False
    
    return True

def main() -> int:
    """
    Main entry point for directory initialization.
    
    Returns:
        0 on success, 1 on failure.
    """
    logger = get_logger(__name__)
    logger.info("Starting directory initialization...")
    
    # Determine project root (assuming script is in code/ directory)
    script_path = Path(__file__).resolve()
    project_root = script_path.parent.parent
    
    try:
        create_directories(project_root)
        
        if verify_structure(project_root):
            logger.info("Directory initialization completed successfully.")
            return 0
        else:
            logger.error("Directory verification failed.")
            return 1
            
    except Exception as e:
        logger.error(f"Error during directory initialization: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
