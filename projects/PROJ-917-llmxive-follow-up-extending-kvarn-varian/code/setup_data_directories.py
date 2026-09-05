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

def get_project_root() -> Path:
    """
    Determines the project root directory.
    Assumes the script is run from the project root or 'code/' subdirectory.
    """
    current_path = Path.cwd()
    # If running from code/, go up one level
    if current_path.name == 'code':
        return current_path.parent
    # If running from root, check if 'data' exists here
    if (current_path / 'data').exists():
        return current_path
    # Fallback: assume current is root if 'requirements.txt' exists
    if (current_path / 'requirements.txt').exists():
        return current_path
    
    # If none found, default to current directory
    logger.warning("Could not determine project root via standard markers. Using cwd.")
    return current_path

def create_directories() -> bool:
    """
    Creates the data directory structure: data/raw, data/processed, data/results.
    
    Returns:
        bool: True if all directories were created successfully, False otherwise.
    """
    project_root = get_project_root()
    data_root = project_root / 'data'
    
    subdirectories = ['raw', 'processed', 'results']
    created_paths = []
    
    try:
        # Ensure the root data directory exists
        data_root.mkdir(parents=True, exist_ok=True)
        logger.info(f"Ensured data root directory exists: {data_root}")
        
        for subdir in subdirectories:
            target_path = data_root / subdir
            target_path.mkdir(parents=True, exist_ok=True)
            created_paths.append(target_path)
            logger.info(f"Created directory: {target_path}")
        
        return True
    except PermissionError as e:
        logger.error(f"Permission denied while creating directories: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error while creating directories: {e}")
        return False

def verify_structure() -> bool:
    """
    Verifies that the required data directory structure exists.
    
    Returns:
        bool: True if all required directories exist, False otherwise.
    """
    project_root = get_project_root()
    data_root = project_root / 'data'
    
    required_subdirs = ['raw', 'processed', 'results']
    
    if not data_root.exists():
        logger.error(f"Data root directory does not exist: {data_root}")
        return False
    
    all_exist = True
    for subdir in required_subdirs:
        target_path = data_root / subdir
        if not target_path.is_dir():
            logger.error(f"Required subdirectory missing: {target_path}")
            all_exist = False
        else:
            logger.debug(f"Verified directory: {target_path}")
    
    return all_exist

def main():
    """
    Main entry point for the script.
    Creates directories and verifies the structure.
    """
    logger.info("Starting data directory setup...")
    
    success = create_directories()
    if not success:
        logger.error("Failed to create data directories.")
        sys.exit(1)
    
    if verify_structure():
        logger.info("Data directory structure verified successfully.")
        print("SUCCESS: Data directories created and verified.")
        sys.exit(0)
    else:
        logger.error("Data directory structure verification failed.")
        sys.exit(1)

if __name__ == '__main__':
    main()