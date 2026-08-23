import os
import sys
from pathlib import Path
import logging

from utils.logging import get_logger

logger = get_logger(__name__)


def ensure_tests_directory(base_path: str = "tests") -> bool:
    """
    Create the tests directory if it does not exist.
    
    Args:
        base_path: Relative path to the tests directory.
        
    Returns:
        True if the directory exists after the operation, False otherwise.
    """
    path = Path(base_path)
    
    if path.exists():
        logger.info(f"Tests directory already exists at: {path.absolute()}")
        return True
    
    try:
        path.mkdir(parents=True, exist_ok=True)
        logger.info(f"Created tests directory at: {path.absolute()}")
        return True
    except OSError as e:
        logger.error(f"Failed to create tests directory at {path.absolute()}: {e}")
        return False


def main() -> int:
    """
    Main entry point for the script.
    
    Returns:
        0 on success, 1 on failure.
    """
    success = ensure_tests_directory()
    
    if not success:
        logger.error("Verification failed: tests directory does not exist.")
        return 1
        
    # Verification step as per task requirements
    if not os.path.isdir("tests"):
        logger.error("Verification failed: os.path.isdir('tests') returned False.")
        return 1
        
    logger.info("Verification passed: tests directory exists.")
    return 0


if __name__ == "__main__":
    sys.exit(main())