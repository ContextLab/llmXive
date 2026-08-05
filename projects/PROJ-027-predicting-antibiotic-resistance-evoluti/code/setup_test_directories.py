import os
import sys
from pathlib import Path
from utils.logging import get_logger

def create_test_directories():
    """Create the test directory structure with .gitkeep files."""
    logger = get_logger()
    base_path = Path(__file__).resolve().parent.parent
    
    # Define the test directories to create
    test_dirs = [
        "tests/contract",
        "tests/unit",
        "tests/integration"
    ]
    
    created_count = 0
    for dir_path in test_dirs:
        full_path = base_path / dir_path
        try:
            full_path.mkdir(parents=True, exist_ok=True)
            gitkeep_path = full_path / ".gitkeep"
            
            # Create .gitkeep file if it doesn't exist
            if not gitkeep_path.exists():
                gitkeep_path.touch()
                logger.info(f"Created directory: {full_path} and .gitkeep file")
            else:
                logger.info(f"Directory already exists: {full_path}")
            
            created_count += 1
        except OSError as e:
            logger.error(f"Failed to create directory {full_path}: {e}")
    
    logger.info(f"Successfully created/verified {created_count} test directories")
    return created_count

def verify_test_directories():
    """Verify that all required test directories exist."""
    logger = get_logger()
    base_path = Path(__file__).resolve().parent.parent
    
    required_dirs = [
        "tests/contract",
        "tests/unit",
        "tests/integration"
    ]
    
    all_exist = True
    for dir_path in required_dirs:
        full_path = base_path / dir_path
        gitkeep_path = full_path / ".gitkeep"
        
        if full_path.exists() and full_path.is_dir():
            if gitkeep_path.exists():
                logger.info(f"Verified: {full_path} with .gitkeep")
            else:
                logger.warning(f"Directory exists but missing .gitkeep: {full_path}")
                all_exist = False
        else:
            logger.error(f"Missing directory: {full_path}")
            all_exist = False
    
    return all_exist

def main():
    """Main entry point for test directory setup."""
    logger = get_logger()
    logger.info("Starting test directory setup...")
    
    create_test_directories()
    
    if verify_test_directories():
        logger.info("Test directory setup completed successfully.")
        return 0
    else:
        logger.error("Test directory setup completed with errors.")
        return 1

if __name__ == "__main__":
    sys.exit(main())