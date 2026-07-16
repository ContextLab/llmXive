"""
Directory Structure Setup for PROJ-800-assessing-parcellation-sensitivity-of-hu.

This script ensures the existence of all required project directories
as specified in the implementation plan and tasks.md.

Required directories:
- data/raw: For raw downloaded fMRI data (NIfTI files)
- data/processed: For intermediate processed data (time series, masks, mappings)
- data/results: For final analysis results, metrics, and reports
- code/: For source code (already exists, but ensured for completeness)
- tests/: For test suites (already exists, but ensured for completeness)
"""
import os
import sys
from pathlib import Path

# Import the logger utility from the existing codebase
from utils.logger import get_logger, ConfigurationError

logger = get_logger(__name__)

def ensure_directory(path: Path) -> None:
    """
    Ensure a directory exists. Create it if it doesn't.

    Args:
        path: Path object representing the directory to ensure.

    Raises:
        ConfigurationError: If the directory cannot be created or is not writable.
    """
    if not path.exists():
        logger.info(f"Creating directory: {path}")
        try:
            path.mkdir(parents=True, exist_ok=True)
            # Verify it was actually created
            if not path.exists():
                raise ConfigurationError(f"Failed to create directory: {path}")
            # Verify write permissions
            if not os.access(path, os.W_OK):
                raise ConfigurationError(f"Directory created but not writable: {path}")
        except OSError as e:
            raise ConfigurationError(f"OS error while creating directory {path}: {e}")
    else:
        if not path.is_dir():
            raise ConfigurationError(f"Path exists but is not a directory: {path}")
        logger.debug(f"Directory already exists: {path}")

def main() -> None:
    """
    Main entry point to set up the project directory structure.

    This function creates all required directories relative to the project root.
    It uses the current working directory as the project root.
    """
    project_root = Path.cwd()
    logger.info(f"Setting up directory structure for project at: {project_root}")

    # Define required directories relative to project root
    required_dirs = [
        project_root / "data" / "raw",
        project_root / "data" / "processed",
        project_root / "data" / "results",
        project_root / "code",
        project_root / "tests",
    ]

    # Also ensure the standard subdirectories for organization
    additional_dirs = [
        project_root / "data" / "interim",  # Optional, for intermediate states
        project_root / "code" / "utils",
        project_root / "code" / "models",
        project_root / "tests" / "unit",
        project_root / "tests" / "integration",
        project_root / "tests" / "contract",
    ]

    all_dirs = required_dirs + additional_dirs

    errors = []
    for dir_path in all_dirs:
        try:
            ensure_directory(dir_path)
        except ConfigurationError as e:
            errors.append(str(e))
            logger.error(f"Failed to setup {dir_path}: {e}")

    if errors:
        logger.error(f"Directory setup completed with {len(errors)} errors.")
        sys.exit(1)
    else:
        logger.info("Directory structure setup completed successfully.")
        # List created directories for verification
        created_dirs = [str(d.relative_to(project_root)) for d in all_dirs if d.exists()]
        logger.info(f"Verified directories: {', '.join(created_dirs)}")

if __name__ == "__main__":
    main()