"""
Task T001a: Create project directories for llmXive Follow-up project.

Creates the following directories relative to the repository root:
- projects/PROJ-967-llmxive-follow-up-extending-beyond-scala/data/raw
- projects/PROJ-967-llmxive-follow-up-extending-beyond-scala/data/processed
- projects/PROJ-967-llmxive-follow-up-extending-beyond-scala/code
- projects/PROJ-967-llmxive-follow-up-extending-beyond-scala/tests
- projects/PROJ-967-llmxive-follow-up-extending-beyond-scala/results

This script replaces T004 and ensures all necessary directories exist
before other pipeline tasks can execute.
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

def ensure_directory(path: Path) -> bool:
    """
    Create a directory if it doesn't exist.
    
    Args:
        path: Path object representing the directory to create
        
    Returns:
        True if directory exists or was created successfully, False otherwise
    """
    try:
        if not path.exists():
            path.mkdir(parents=True, exist_ok=True)
            logger.info(f"Created directory: {path}")
        else:
            logger.info(f"Directory already exists: {path}")
        return True
    except Exception as e:
        logger.error(f"Failed to create directory {path}: {e}")
        return False

def main():
    """
    Main function to create all required project directories.
    """
    # Define the base project path
    base_path = Path("projects/PROJ-967-llmxive-follow-up-extending-beyond-scala")
    
    # Define all required directories
    directories = [
        base_path / "data" / "raw",
        base_path / "data" / "processed",
        base_path / "code",
        base_path / "tests",
        base_path / "results"
    ]
    
    logger.info(f"Creating project structure under: {base_path}")
    
    success_count = 0
    total_count = len(directories)
    
    for directory in directories:
        if ensure_directory(directory):
            success_count += 1
    
    logger.info(f"Directory creation complete: {success_count}/{total_count} successful")
    
    if success_count == total_count:
        logger.info("All required directories created successfully.")
        return 0
    else:
        logger.error(f"Failed to create {total_count - success_count} directories.")
        return 1

if __name__ == "__main__":
    sys.exit(main())