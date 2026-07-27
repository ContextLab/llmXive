"""
Task T001a: Create project directories for llmXive Follow-up.
Creates the required directory structure under projects/PROJ-967-llmxive-follow-up-extending-beyond-scala/
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

# Project root relative to where this script is run (assumed to be repo root)
# The task specifies paths relative to repository root.
PROJECT_ROOT = Path(__file__).resolve().parent.parent
PROJECT_DIR = PROJECT_ROOT / "projects" / "PROJ-967-llmxive-follow-up-extending-beyond-scala"

# Directories to create as per T001a
DIRECTORIES = [
    "data/raw",
    "data/processed",
    "code",
    "tests",
    "results"
]

def ensure_directory(dir_path: Path) -> bool:
    """
    Ensures a directory exists. Creates it if it doesn't.
    
    Args:
        dir_path: Path object representing the directory to create.
        
    Returns:
        True if directory exists or was created successfully, False otherwise.
    """
    try:
        if not dir_path.exists():
            dir_path.mkdir(parents=True, exist_ok=True)
            logger.info(f"Created directory: {dir_path}")
        else:
            logger.info(f"Directory already exists: {dir_path}")
        return True
    except Exception as e:
        logger.error(f"Failed to create directory {dir_path}: {e}")
        return False

def main():
    """
    Main entry point for T001a.
    Creates all required project directories.
    """
    logger.info(f"Starting directory creation for project: {PROJECT_DIR}")
    
    success = True
    for subdir in DIRECTORIES:
        full_path = PROJECT_DIR / subdir
        if not ensure_directory(full_path):
            success = False
    
    if success:
        logger.info("All directories created successfully.")
        # Print summary for verification
        print(f"\nProject structure created at: {PROJECT_DIR}")
        for subdir in DIRECTORIES:
            print(f"  - {PROJECT_DIR / subdir}")
        return 0
    else:
        logger.error("Some directories failed to create.")
        return 1

if __name__ == "__main__":
    sys.exit(main())