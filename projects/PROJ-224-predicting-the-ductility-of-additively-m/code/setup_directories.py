"""
Setup script to create the required project directory structure.
Ensures all necessary folders exist before data processing begins.
"""
import os
import sys
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def create_directories():
    """Create all required directories for the project."""
    project_root = Path(__file__).resolve().parent.parent
    directories = [
        "code",
        "code/data",
        "code/models",
        "code/analysis",
        "code/tests",
        "data",
        "data/validation",
        "data/reports",
        "artifacts",
        "state",
        "state/projects/PROJ-224-predicting-the-ductility-of-additively-m"
    ]

    created = 0
    for dir_name in directories:
        dir_path = project_root / dir_name
        if not dir_path.exists():
            dir_path.mkdir(parents=True, exist_ok=True)
            logger.info(f"Created directory: {dir_path}")
            created += 1
        else:
            logger.debug(f"Directory exists: {dir_path}")

    logger.info(f"Directory setup complete. Created {created} new directories.")
    return True

def main():
    try:
        create_directories()
        logger.info("Setup directories stage completed successfully.")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Setup directories stage failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
