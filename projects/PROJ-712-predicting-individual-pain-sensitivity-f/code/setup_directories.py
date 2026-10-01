"""
Script to initialize the project directory structure for llmXive PROJ-712.

Creates the required directories:
- data/raw/
- data/processed/
- artifacts/
- state/
- code/
- tests/

This script is idempotent and will not fail if directories already exist.
"""
import os
import sys
from pathlib import Path
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def ensure_directories():
    """
    Create the standard project directory structure.
    
    Returns:
        list: List of created directory paths as strings.
    """
    # Define the project root relative to this script's location
    # Assuming this script is at code/setup_directories.py
    # The project root is the parent of 'code'
    current_file = Path(__file__).resolve()
    project_root = current_file.parent.parent
    
    required_dirs = [
        project_root / "data" / "raw",
        project_root / "data" / "processed",
        project_root / "artifacts",
        project_root / "state",
        project_root / "code",
        project_root / "tests"
    ]
    
    created = []
    for dir_path in required_dirs:
        if not dir_path.exists():
            dir_path.mkdir(parents=True, exist_ok=True)
            logger.info(f"Created directory: {dir_path}")
            created.append(str(dir_path))
        else:
            logger.debug(f"Directory already exists: {dir_path}")
    
    return created

def validate_paths():
    """
    Validate that the required directories exist.
    
    Returns:
        bool: True if all directories exist, False otherwise.
    """
    current_file = Path(__file__).resolve()
    project_root = current_file.parent.parent
    
    required_dirs = [
        project_root / "data" / "raw",
        project_root / "data" / "processed",
        project_root / "artifacts",
        project_root / "state",
        project_root / "code",
        project_root / "tests"
    ]
    
    missing = []
    for dir_path in required_dirs:
        if not dir_path.exists():
            missing.append(str(dir_path))
    
    if missing:
        logger.error(f"Missing required directories: {missing}")
        return False
    
    logger.info("All required directories are present.")
    return True

def main():
    """Main entry point for the directory setup script."""
    logger.info("Starting project directory initialization...")
    
    created = ensure_directories()
    
    if created:
        logger.info(f"Successfully created {len(created)} directories.")
    else:
        logger.info("No new directories were created (all already exist).")
    
    # Validate the structure
    if not validate_paths():
        logger.error("Validation failed. Some directories are missing.")
        sys.exit(1)
    
    logger.info("Project directory structure initialized successfully.")

if __name__ == "__main__":
    main()