import os
import sys
from pathlib import Path
from utils.logging import get_logger

def create_data_directories():
    """
    Create the required data directory structure:
    data/raw/
    data/processed/
    data/models/
    
    Also creates .gitkeep files in each to ensure they are tracked by git.
    """
    logger = get_logger()
    base_dir = Path("data")
    
    directories = [
        base_dir / "raw",
        base_dir / "processed",
        base_dir / "models",
    ]
    
    for directory in directories:
        if not directory.exists():
            directory.mkdir(parents=True, exist_ok=True)
            logger.info(f"Created directory: {directory}")
        
        # Create .gitkeep file to ensure directory is tracked
        gitkeep_path = directory / ".gitkeep"
        if not gitkeep_path.exists():
            gitkeep_path.touch()
            logger.info(f"Created .gitkeep in: {directory}")
        else:
            logger.debug(f".gitkeep already exists in: {directory}")
    
    return True

def verify_data_directories():
    """
    Verify that all required data directories exist.
    Returns True if all directories exist, False otherwise.
    """
    logger = get_logger()
    base_dir = Path("data")
    
    required_dirs = [
        base_dir / "raw",
        base_dir / "processed",
        base_dir / "models",
    ]
    
    all_exist = True
    for directory in required_dirs:
        if directory.exists() and directory.is_dir():
            logger.info(f"Verified directory exists: {directory}")
        else:
            logger.error(f"Directory missing: {directory}")
            all_exist = False
    
    return all_exist

def main():
    """
    Main entry point for data directory setup.
    """
    logger = get_logger()
    logger.info("Starting data directory setup...")
    
    # Create directories
    create_success = create_data_directories()
    
    if not create_success:
        logger.error("Failed to create data directories")
        return 1
    
    # Verify directories
    if verify_data_directories():
        logger.info("Data directory setup completed successfully")
        return 0
    else:
        logger.error("Data directory verification failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())
