import os
import sys
from pathlib import Path
import logging

from utils.logging import get_logger

logger = get_logger(__name__)


def ensure_data_directory(path: str = "data") -> bool:
    """
    Ensure a specific data directory exists.
    
    Args:
        path: Relative path to the directory.
        
    Returns:
        True if the directory exists, False otherwise.
    """
    dir_path = Path(path)
    
    if not dir_path.exists():
        try:
            dir_path.mkdir(parents=True, exist_ok=True)
            logger.info(f"Created directory: {dir_path.absolute()}")
            return True
        except OSError as e:
            logger.error(f"Failed to create directory {path}: {e}")
            return False
    
    logger.info(f"Directory already exists: {dir_path.absolute()}")
    return True


def main() -> int:
    """
    Main entry point.
    
    Returns:
        0 on success, 1 on failure.
    """
    if not ensure_data_directory():
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())