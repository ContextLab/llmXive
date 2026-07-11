"""
Task T001: Create the project root directory.

This script ensures the existence of the project root directory:
projects/PROJ-446-predicting-molecular-halide-binding-affi/
"""
import os
from pathlib import Path
from code.utils.logger import get_logger

logger = get_logger(__name__)

PROJECT_ROOT_NAME = "PROJ-446-predicting-molecular-halide-binding-affi"
PROJECTS_PARENT = Path("projects")

def main():
    """Create the project root directory if it does not exist."""
    target_dir = PROJECTS_PARENT / PROJECT_ROOT_NAME

    if target_dir.exists():
        logger.info(f"Directory already exists: {target_dir}")
        return True

    try:
        target_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"Successfully created directory: {target_dir}")
        return True
    except OSError as e:
        logger.error(f"Failed to create directory {target_dir}: {e}")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
