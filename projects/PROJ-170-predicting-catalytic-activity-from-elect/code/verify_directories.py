import os
import sys
import logging
from pathlib import Path
from config import get_project_root, get_data_path, get_output_path

def verify_directories() -> bool:
    """
    Verify existence of all required directories from T001a.
    
    Required directories:
    - data/raw/
    - data/processed/
    - code/
    - outputs/
    - tests/
    - state/projects/
    - code/models/
    
    Returns:
        bool: True if all directories exist, False otherwise.
        
    Raises:
        RuntimeError: If any required directory is missing.
    """
    project_root = get_project_root()
    logger = logging.getLogger(__name__)
    
    # Define required directories relative to project root
    required_dirs = [
        "data/raw",
        "data/processed",
        "code",
        "outputs",
        "tests",
        "state/projects",
        "code/models"
    ]
    
    missing_dirs = []
    
    for dir_path in required_dirs:
        full_path = project_root / dir_path
        if not full_path.exists():
            missing_dirs.append(dir_path)
            logger.error(f"Missing required directory: {full_path}")
        elif not full_path.is_dir():
            missing_dirs.append(dir_path)
            logger.error(f"Path exists but is not a directory: {full_path}")
        else:
            logger.info(f"Verified directory exists: {full_path}")
    
    if missing_dirs:
        error_msg = (
            f"Verification failed. Missing {len(missing_dirs)} required directories:\n"
            + "\n".join([f"  - {d}" for d in missing_dirs])
        )
        logger.error(error_msg)
        raise RuntimeError(error_msg)
    
    logger.info("All required directories verified successfully.")
    return True

def main():
    """Entry point for directory verification."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    try:
        verify_directories()
        print("SUCCESS: All required directories exist.")
        sys.exit(0)
    except RuntimeError as e:
        print(f"FAILURE: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()