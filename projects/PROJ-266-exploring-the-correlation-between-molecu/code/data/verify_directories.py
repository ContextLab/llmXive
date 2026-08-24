"""
Verification script for directory structure.
Implements T008c: Verify directory structure.
"""
import os
import sys
from pathlib import Path
from utils.config import get_project_root
from utils.logging import get_logger, configure_root_logger

logger = get_logger(__name__)

def verify_directories() -> bool:
    """
    Verify that required directories exist.
    Executes assertions for T008c.
    
    Returns:
        True if all directories exist, False otherwise.
    """
    project_root = get_project_root()
    logger.info(f"Project root: {project_root}")
    
    # Define required directories relative to project root
    required_dirs = [
        project_root / "data" / "raw",
        project_root / "data" / "processed"
    ]
    
    all_valid = True
    
    for dir_path in required_dirs:
        if not dir_path.exists():
            logger.error(f"Directory does not exist: {dir_path}")
            all_valid = False
        elif not dir_path.is_dir():
            logger.error(f"Path exists but is not a directory: {dir_path}")
            all_valid = False
        else:
            logger.info(f"Verified directory: {dir_path}")
    
    # Execute the specific assertions required by T008c
    # These will raise AssertionError if directories are missing
    try:
        assert os.path.isdir(str(project_root / "data" / "raw")), \
            f"Directory 'data/raw' does not exist at {project_root / 'data' / 'raw'}"
        logger.info("Assertion passed: data/raw exists")
        
        assert os.path.isdir(str(project_root / "data" / "processed")), \
            f"Directory 'data/processed' does not exist at {project_root / 'data' / 'processed'}"
        logger.info("Assertion passed: data/processed exists")
        
    except AssertionError as e:
        logger.error(f"Verification failed: {e}")
        return False
    
    return True

def main() -> int:
    """Main entry point for directory verification."""
    configure_root_logger()
    logger.info("Starting directory structure verification (T008c)")
    
    if verify_directories():
        logger.info("Directory structure verification PASSED")
        return 0
    else:
        logger.error("Directory structure verification FAILED")
        return 1

if __name__ == "__main__":
    sys.exit(main())
