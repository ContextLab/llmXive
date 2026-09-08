"""
Task T009: Create and verify required project directories.

This script ensures the existence of data/processed/, models/, and reports/
directories. It relies on T001 (setup_project.py) to have created the
base structure (code/, data/, tests/, state/, data/raw/).

It verifies the existence of:
- data/raw/ (created by T001)
- data/processed/ (created here if missing)
- models/ (created here if missing)
- reports/ (created here if missing)

If any directory cannot be created or verified, the script exits with a 
non-zero status code.
"""
import os
import sys
from pathlib import Path
import logging

# Configure logging to match project standards (code/logging_config.py expected)
# If logging_config.py is not yet fully functional, we fallback to basic config
try:
    from logging_config import setup_logging
    setup_logging()
except ImportError:
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

logger = logging.getLogger(__name__)

def ensure_directory(path: Path) -> bool:
    """Create directory if it doesn't exist and verify it exists."""
    try:
        if not path.exists():
            path.mkdir(parents=True, exist_ok=True)
            logger.info(f"Created directory: {path}")
        
        if not path.is_dir():
            logger.error(f"Path exists but is not a directory: {path}")
            return False
          
        logger.info(f"Verified directory: {path}")
        return True
    except OSError as e:
        logger.error(f"Failed to create/verify directory {path}: {e}")
        return False

def main():
    """Main entry point for T009."""
    logger.info("Starting T009: Directory creation and verification")
    
    # Define required directories relative to project root
    # T001 should have created: code/, data/, tests/, state/, data/raw/
    # T009 focuses on: data/processed/, models/, reports/
    required_dirs = [
        Path("data/raw"),        # Prerequisite from T001
        Path("data/processed"),  # T009 target
        Path("models"),          # T009 target
        Path("reports"),         # T009 target
    ]
    
    all_success = True
    
    for dir_path in required_dirs:
        if not ensure_directory(dir_path):
            all_success = False
    
    if all_success:
        logger.info("T009 completed successfully: All directories verified.")
        # Print a simple listing for verification output
        print("\n--- Directory Verification Report ---")
        for dir_path in required_dirs:
            if dir_path.exists() and dir_path.is_dir():
                print(f"[OK] {dir_path}")
            else:
                print(f"[FAIL] {dir_path}")
        print("-------------------------------------\n")
        return 0
    else:
        logger.error("T009 failed: Some directories could not be verified.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
