import os
import sys
from pathlib import Path
import logging

from config import get_logger, setup_logging

logger = get_logger(__name__)

def main():
    """
    Create the full project directory tree for PROJ-191.
    This script ensures all required directories exist atomically.
    """
    # Define the project root based on the task description
    # The task specifies: projects/PROJ-191-investigating-the-validity-of-the-invers/
    # We assume this runs from the repository root.
    repo_root = Path(__file__).resolve().parent.parent
    project_name = "PROJ-191-investigating-the-validity-of-the-invers"
    project_root = repo_root / "projects" / project_name

    # Define all required subdirectories
    # Core structure
    core_dirs = [
        "code",
        "tests",
        "data",
        "docs",
    ]

    # Code sub-structure
    code_dirs = [
        "code/data",
        "code/models",
        "code/inference",
        "code/robustness",
        "code/utils",
    ]

    # Data sub-structure
    data_dirs = [
        "data/raw",
        "data/processed",
        "data/results",
    ]

    # Tests sub-structure
    tests_dirs = [
        "tests/unit",
        "tests/contract",
        "tests/integration",
    ]

    # Combine all relative paths
    all_dirs = core_dirs + code_dirs + data_dirs + tests_dirs

    # Ensure parent directory exists
    project_root.mkdir(parents=True, exist_ok=True)
    logger.info(f"Project root ensured: {project_root}")

    # Create each directory
    created_count = 0
    for rel_path in all_dirs:
        dir_path = project_root / rel_path
        dir_path.mkdir(parents=True, exist_ok=True)
        created_count += 1
        logger.debug(f"Created directory: {dir_path}")

    logger.info(f"Successfully created {created_count} directories for {project_name}")
    
    # Verify structure
    missing = []
    for rel_path in all_dirs:
        if not (project_root / rel_path).exists():
            missing.append(rel_path)
    
    if missing:
        logger.error(f"Missing directories: {missing}")
        return 1
    
    logger.info("Directory structure verification passed.")
    return 0

if __name__ == "__main__":
    setup_logging()
    sys.exit(main())
