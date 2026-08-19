"""
Script to create the project directory structure as defined in the implementation plan.
"""
import os
from pathlib import Path
import logging
from config import get_project_root

# Configure logging for this script
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("setup_directories")

def setup_directories():
    """
    Creates the required directory tree for the project.
    Structure:
    code/
      data/
      stimuli/
      analysis/
      viz/
      tests/
    data/
      raw/stimuli/
      raw/responses/
      processed/
      results/
    docs/
    """
    project_root = get_project_root()
    logger.info(f"Project root identified at: {project_root}")

    # Define relative paths to create
    directories = [
        "code/data",
        "code/stimuli",
        "code/analysis",
        "code/viz",
        "code/tests",
        "data/raw/stimuli",
        "data/raw/responses",
        "data/processed",
        "data/results",
        "docs"
    ]

    created_count = 0
    for rel_dir in directories:
        full_path = project_root / rel_dir
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            logger.info(f"Created directory: {full_path}")
            created_count += 1
        else:
            logger.debug(f"Directory already exists: {full_path}")

    logger.info(f"Setup complete. Created {created_count} new directories.")
    return True

def main():
    """Entry point for the script."""
    try:
        setup_directories()
        print("Directory structure created successfully.")
    except Exception as e:
        logger.error(f"Failed to create directories: {e}")
        raise

if __name__ == "__main__":
    main()