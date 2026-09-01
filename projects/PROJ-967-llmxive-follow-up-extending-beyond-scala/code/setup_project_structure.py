"""
Task T001a: Create project directory structure.
Creates the required directories for the llmXive follow-up project.
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

PROJECT_ROOT = Path("projects/PROJ-967-llmxive-follow-up-extending-beyond-scala")
REQUIRED_DIRS = [
    "data/raw",
    "data/processed",
    "results",
    "code",
    "tests"
]

def ensure_directory(dir_path: Path) -> bool:
    """
    Ensures a directory exists, creating it if necessary.
    
    Args:
        dir_path: Path object representing the directory to create.
        
    Returns:
        True if directory exists or was created successfully, False otherwise.
    """
    try:
        dir_path.mkdir(parents=True, exist_ok=True)
        logger.info(f"Directory created/verified: {dir_path}")
        return True
    except OSError as e:
        logger.error(f"Failed to create directory {dir_path}: {e}")
        return False

def main():
    """
    Main entry point for T001a.
    Creates all required project directories.
    """
    logger.info(f"Starting project structure setup for: {PROJECT_ROOT}")
    
    # Ensure project root exists
    if not ensure_directory(PROJECT_ROOT):
        logger.error("Failed to create project root directory. Exiting.")
        sys.exit(1)
    
    # Create all required subdirectories
    success_count = 0
    for dir_name in REQUIRED_DIRS:
        full_path = PROJECT_ROOT / dir_name
        if ensure_directory(full_path):
            success_count += 1
    
    logger.info(f"Setup complete: {success_count}/{len(REQUIRED_DIRS)} directories created successfully.")
    
    if success_count != len(REQUIRED_DIRS):
        logger.error("Some directories failed to create. Check logs for details.")
        sys.exit(1)
    
    logger.info("All required directories are in place.")
    sys.exit(0)

if __name__ == "__main__":
    main()