"""
Project Directory Initialization Script.
Creates the foundational directory structure required for the llmXive pipeline.
"""
import os
import sys
from pathlib import Path
import logging

# Configure basic logging for the setup phase
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Define the project root relative to this script's location
# Assuming this script is in code/ or code/setup_*.py
# We need to resolve the project root.
# Standard convention: script is at code/setup_directories.py, root is parent of code/
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent

# Directories to create relative to PROJECT_ROOT
DIRECTORIES_TO_CREATE = [
    "code",
    "tests",
    "logs",
    "results",
    "data/raw",
    "data/processed",
    "docs",
    "figures"
]

def ensure_directory(dir_path: Path) -> bool:
    """
    Ensures a directory exists. Creates it if missing.
    Returns True if successful, False otherwise.
    """
    try:
        if not dir_path.exists():
            dir_path.mkdir(parents=True, exist_ok=True)
            logger.info(f"Created directory: {dir_path}")
        else:
            logger.info(f"Directory already exists: {dir_path}")
        
        # Verify writability by attempting to create a temp file
        test_file = dir_path / ".write_test"
        test_file.touch()
        test_file.unlink()
        return True
    except PermissionError:
        logger.error(f"Permission denied: Unable to write to {dir_path}")
        return False
    except OSError as e:
        logger.error(f"OS error creating {dir_path}: {e}")
        return False

def main():
    """
    Main entry point to initialize the project structure.
    """
    logger.info(f"Project Root identified at: {PROJECT_ROOT}")
    
    all_success = True
    created_count = 0
    
    for dir_name in DIRECTORIES_TO_CREATE:
        full_path = PROJECT_ROOT / dir_name
        if ensure_directory(full_path):
            created_count += 1
        else:
            all_success = False
    
    if all_success:
        logger.info(f"Successfully initialized {created_count} directories.")
        sys.exit(0)
    else:
        logger.error("Failed to create one or more required directories.")
        sys.exit(1)

if __name__ == "__main__":
    main()