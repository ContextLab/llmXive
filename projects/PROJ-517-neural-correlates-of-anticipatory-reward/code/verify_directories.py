import os
import sys
from pathlib import Path
import logging

from logging_config import setup_logging, get_logger

REQUIRED_DIRS = [
    "code",
    "tests",
    "data/raw",
    "data/processed",
    "data/figures",
]

def verify_directories(base_path: Path = None) -> bool:
    """
    Verify that all required directories exist.
    If any are missing, raise FileNotFoundError with a specific message.
    
    Args:
        base_path: Base directory to check relative paths against. 
                   Defaults to current working directory.
    
    Returns:
        True if all directories exist.
    
    Raises:
        FileNotFoundError: If any required directory is missing.
    """
    if base_path is None:
        base_path = Path.cwd()
    
    logger = get_logger(__name__)
    missing_dirs = []
    
    for dir_name in REQUIRED_DIRS:
        full_path = base_path / dir_name
        if not full_path.exists():
            missing_dirs.append(str(full_path))
        elif not full_path.is_dir():
            missing_dirs.append(f"{full_path} (exists but is not a directory)")
    
    if missing_dirs:
        error_msg = (
            f"Directory creation failed. Re-run T001a/b/c.\n"
            f"Missing directories:\n" + "\n".join(f"  - {d}" for d in missing_dirs)
        )
        logger.error(error_msg)
        raise FileNotFoundError(error_msg)
    
    logger.info("All required directories verified successfully.")
    return True

def main():
    """
    Entry point for directory verification script.
    Verifies all required directories exist in the project root.
    """
    setup_logging()
    logger = get_logger(__name__)
    
    logger.info("Starting directory verification for T001d...")
    
    try:
        verify_directories()
        logger.info("Verification complete: All directories present.")
        return 0
    except FileNotFoundError as e:
        logger.error(f"Verification failed: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())