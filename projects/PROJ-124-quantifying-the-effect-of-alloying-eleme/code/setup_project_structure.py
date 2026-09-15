"""
Project structure initialization script.
Creates the required directory tree for the llmXive automated science pipeline.
"""
import os
import sys
import subprocess
from pathlib import Path
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def create_project_structure():
    """
    Creates the required directory structure for the project.
    Directories are created relative to the project root.
    """
    # Define the directories to create based on tasks.md T001
    # Note: We assume this script runs from the project root
    project_root = Path(__file__).resolve().parent.parent
    
    directories = [
        "code/data",
        "code/models",
        "code/utils",
        "code/config",
        "data/raw",
        "data/processed",
        "state",
        "output",
        "tests/contract",
        "tests/integration",
        "tests/unit",
        "docs/paper",
        "docs/reports"
    ]
    
    created_count = 0
    for dir_path in directories:
        full_path = project_root / dir_path
        try:
            full_path.mkdir(parents=True, exist_ok=True)
            # Verify writability
            if os.access(full_path, os.W_OK):
                logger.info(f"Created/Verified: {full_path}")
                created_count += 1
            else:
                logger.error(f"Directory created but not writable: {full_path}")
        except Exception as e:
            logger.error(f"Failed to create directory {full_path}: {e}")
            raise

    logger.info(f"Successfully created/verified {created_count} directories.")
    return True

def main():
    """Entry point for the script."""
    logger.info("Starting project structure initialization...")
    try:
        create_project_structure()
        logger.info("Project structure initialization complete.")
        return 0
    except Exception as e:
        logger.error(f"Initialization failed: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
