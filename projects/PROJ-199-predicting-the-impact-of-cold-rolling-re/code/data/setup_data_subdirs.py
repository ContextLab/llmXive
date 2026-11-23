"""
Task T005: Create subdirectories `raw`, `processed`, `interim` within `data/` with `.gitkeep`.

This script ensures the data directory structure required by FR-001 (Data Hygiene)
and Plan.md Project Structure exists. It creates the directories if they do not
exist and places a `.gitkeep` file in each to ensure they are tracked by Git.
"""
import os
import sys
import logging
from pathlib import Path

# Add parent directory to path to allow imports from code package if running as script
# Note: In a standard execution, `code` is in sys.path or installed.
# If running directly as `python code/data/setup_data_subdirs.py`, we need to adjust.
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from utils.logging import get_logger

def create_subdirectories(base_path: Path, subdirs: list[str]) -> None:
    """
    Create subdirectories under base_path and add .gitkeep to each.
    
    Args:
        base_path: The root directory (e.g., data/)
        subdirs: List of subdirectory names to create.
    """
    logger = get_logger(__name__)
    
    for subdir_name in subdirs:
        subdir_path = base_path / subdir_name
        if not subdir_path.exists():
            subdir_path.mkdir(parents=True, exist_ok=True)
            logger.info(f"Created directory: {subdir_path}")
        else:
            logger.debug(f"Directory already exists: {subdir_path}")
        
        gitkeep_path = subdir_path / ".gitkeep"
        if not gitkeep_path.exists():
            gitkeep_path.touch()
            logger.info(f"Created .gitkeep in: {subdir_path}")
        else:
            logger.debug(f".gitkeep already exists in: {subdir_path}")

def verify_subdirectories(base_path: Path, subdirs: list[str]) -> bool:
    """
    Verify that all required subdirectories and .gitkeep files exist.
    
    Args:
        base_path: The root directory (e.g., data/)
        subdirs: List of subdirectory names to check.
        
    Returns:
        True if all exist, False otherwise.
    """
    logger = get_logger(__name__)
    all_good = True
    
    for subdir_name in subdirs:
        subdir_path = base_path / subdir_name
        gitkeep_path = subdir_path / ".gitkeep"
        
        if not subdir_path.is_dir():
            logger.error(f"Missing directory: {subdir_path}")
            all_good = False
        elif not gitkeep_path.exists():
            logger.error(f"Missing .gitkeep in: {subdir_path}")
            all_good = False
        else:
            logger.info(f"Verified: {subdir_path} (contains .gitkeep)")
            
    return all_good

def main():
    """Main entry point for T005."""
    logger = get_logger(__name__)
    logger.info("Starting T005: Setup data subdirectories (raw, processed, interim)")
    
    # Determine the data directory path relative to project root
    # Assuming the script is run from the project root or sys.path is set correctly
    # We look for 'data' relative to the script's location (2 levels up)
    current_file = Path(__file__).resolve()
    code_dir = current_file.parent
    project_root = code_dir.parent
    data_dir = project_root / "data"
    
    required_subdirs = ["raw", "processed", "interim"]
    
    # Ensure the base data directory exists
    if not data_dir.exists():
        logger.warning(f"Base data directory {data_dir} does not exist. Creating it.")
        data_dir.mkdir(parents=True, exist_ok=True)
    
    # Create subdirectories and .gitkeep files
    create_subdirectories(data_dir, required_subdirs)
    
    # Verify
    success = verify_subdirectories(data_dir, required_subdirs)
    
    if success:
        logger.info("T005 completed successfully: All subdirectories and .gitkeep files verified.")
        return 0
    else:
        logger.error("T005 failed: Verification failed.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
