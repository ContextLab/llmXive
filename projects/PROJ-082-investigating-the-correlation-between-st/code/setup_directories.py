import os
import sys
from pathlib import Path
from utils.logger import get_logger

def create_directories():
    """
    Initialize project directory structure.
    Creates code/, tests/, data/, and docs/ directories in a single step.
    """
    logger = get_logger("setup_directories")
    project_root = Path.cwd()
    
    directories = [
        "code",
        "tests",
        "data",
        "docs"
    ]
    
    created = []
    for dir_name in directories:
        dir_path = project_root / dir_name
        if not dir_path.exists():
          dir_path.mkdir(parents=True, exist_ok=True)
          created.append(dir_name)
          logger.info(f"Created directory: {dir_path}")
        else:
          logger.info(f"Directory already exists: {dir_path}")
    
    # Ensure data subdirectories exist for pipeline outputs
    data_subdirs = ["raw", "derived", "interim"]
    data_path = project_root / "data"
    for subdir in data_subdirs:
        subdir_path = data_path / subdir
        if not subdir_path.exists():
            subdir_path.mkdir(parents=True, exist_ok=True)
            created.append(f"data/{subdir}")
            logger.info(f"Created subdirectory: {subdir_path}")
    
    # Ensure tests subdirectories exist
    test_subdirs = ["unit", "integration", "contract"]
    tests_path = project_root / "tests"
    for subdir in test_subdirs:
        subdir_path = tests_path / subdir
        if not subdir_path.exists():
            subdir_path.mkdir(parents=True, exist_ok=True)
            created.append(f"tests/{subdir}")
            logger.info(f"Created subdirectory: {subdir_path}")

    if not created:
        logger.info("All required directories already existed.")
    else:
        logger.info(f"Successfully created {len(created)} directories.")
    
    return created

def verify_structure():
    """
    Verify that the required directory structure exists.
    Returns True if all directories are present, False otherwise.
    """
    project_root = Path.cwd()
    required_dirs = [
        "code",
        "tests",
        "data",
        "docs",
        "data/raw",
        "data/derived",
        "data/interim",
        "tests/unit",
        "tests/integration",
        "tests/contract"
    ]
    
    missing = []
    for dir_name in required_dirs:
        dir_path = project_root / dir_name
        if not dir_path.is_dir():
            missing.append(dir_name)
    
    if missing:
        return False, missing
    return True, []

def main():
    """Entry point for directory setup."""
    logger = get_logger("setup_directories")
    logger.info("Starting directory structure initialization...")
    
    try:
        created = create_directories()
        is_valid, missing = verify_structure()
        
        if is_valid:
            logger.info("Directory structure verification PASSED.")
            return 0
        else:
            logger.error(f"Directory structure verification FAILED. Missing: {missing}")
            return 1
    except Exception as e:
        logger.error(f"Error during directory setup: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
