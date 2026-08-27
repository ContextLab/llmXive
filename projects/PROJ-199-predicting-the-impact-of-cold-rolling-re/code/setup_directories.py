"""
Module to verify and initialize the required project directory structure.
This module ensures that 'code/', 'data/', 'tests/', and 'docs/' directories exist.
"""
import os
import sys
from pathlib import Path
import logging

from utils.logging import get_logger

logger = get_logger(__name__)

def ensure_directory_exists(dir_name: str, base_path: Path = None) -> bool:
    """
    Ensure a specific directory exists. If it doesn't, create it.
    
    Args:
        dir_name: Name of the directory to ensure exists.
        base_path: Base path to resolve the directory against. Defaults to project root.
        
    Returns:
        True if directory exists (was created or already present), False otherwise.
    """
    if base_path is None:
        base_path = Path(__file__).parent.parent
    
    target_dir = base_path / dir_name
    
    if not target_dir.exists():
        try:
            target_dir.mkdir(parents=True, exist_ok=True)
            logger.info(f"Created directory: {target_dir}")
            return True
        except Exception as e:
            logger.error(f"Failed to create directory {target_dir}: {e}")
            return False
    else:
        logger.debug(f"Directory already exists: {target_dir}")
        return True

def main():
    """
    Main entry point to verify and create the required directory structure.
    """
    logger.info("Starting directory verification and creation...")
    
    base_path = Path(__file__).parent.parent
    required_dirs = ['code', 'data', 'tests', 'docs']
    
    all_success = True
    for dir_name in required_dirs:
        success = ensure_directory_exists(dir_name, base_path)
        if not success:
            all_success = False
            logger.error(f"Failed to ensure existence of directory: {dir_name}")
        else:
            logger.info(f"Successfully verified/created directory: {dir_name}")
    
    if all_success:
        logger.info("All required directories are present.")
        return 0
    else:
        logger.error("Some directories could not be created or verified.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
