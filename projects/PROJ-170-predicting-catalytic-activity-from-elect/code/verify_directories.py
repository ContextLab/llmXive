"""
Directory Verification Script.
Ensures all required project directories exist and logs the result.
"""
import os
import sys
import logging
from pathlib import Path
from config import get_project_root, get_data_path, get_output_path

def setup_verification_logging():
    """Setup logging for the verification script."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler(get_output_path() / "directory_verification.log")
        ]
    )
    return logging.getLogger("verify_directories")

REQUIRED_DIRS = [
    "data/raw",
    "data/processed",
    "code",
    "outputs",
    "tests",
    "state/projects",
    "code/models",
    "code/utils",
    "code/configs",
    "figures"
]

def verify_directories():
    """
    Verify that all required directories exist.
    Raises FileNotFoundError if any are missing.
    """
    logger = setup_verification_logging()
    project_root = get_project_root()
    
    logger.info(f"Verifying directory structure at: {project_root}")
    missing_dirs = []

    for dir_path in REQUIRED_DIRS:
        full_path = project_root / dir_path
        if not full_path.exists():
            missing_dirs.append(dir_path)
            logger.warning(f"MISSING: {full_path}")
        else:
            logger.info(f"OK: {full_path}")

    if missing_dirs:
        error_msg = f"CRITICAL: Missing required directories: {missing_dirs}"
        logger.error(error_msg)
        raise FileNotFoundError(error_msg)

    logger.info("SUCCESS: All required directories exist.")
    return True

def main():
    """Main entry point."""
    try:
        verify_directories()
        return 0
    except Exception as e:
        print(f"Verification failed: {e}", file=sys.stderr)
        return 1

if __name__ == "__main__":
    sys.exit(main())
