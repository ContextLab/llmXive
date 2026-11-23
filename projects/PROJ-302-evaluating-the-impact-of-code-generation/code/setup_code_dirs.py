"""
Setup script to create the required code subdirectories for the llmXive project.

This script creates the following directories under the project root:
- code/data_acquisition/
- code/feature_extraction/
- code/analysis/
- code/utils/

It is designed to be idempotent (safe to run multiple times).
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

def create_directories(base_path: Path, subdirs: list) -> None:
    """
    Create a list of subdirectories under the given base path.
    
    Args:
        base_path: The root directory to create subdirectories under.
        subdirs: List of relative directory paths to create.
    """
    for subdir in subdirs:
        dir_path = base_path / subdir
        try:
            dir_path.mkdir(parents=True, exist_ok=True)
            logger.info(f"Created directory: {dir_path}")
        except OSError as e:
            logger.error(f"Failed to create directory {dir_path}: {e}")
            raise

def main():
    """Main entry point for the script."""
    # Determine the project root (parent of the 'code' directory)
    # Assuming this script is located at code/setup_code_dirs.py
    current_file = Path(__file__).resolve()
    project_root = current_file.parent.parent
    
    logger.info(f"Project root identified as: {project_root}")
    
    # Define the required subdirectories relative to the 'code' directory
    code_dir = project_root / "code"
    
    required_subdirs = [
        "data_acquisition",
        "feature_extraction",
        "analysis",
        "utils"
    ]
    
    logger.info(f"Creating subdirectories under {code_dir}...")
    create_directories(code_dir, required_subdirs)
    
    logger.info("Directory setup completed successfully.")

if __name__ == "__main__":
    main()