"""
Script to create the core project directory structure required for the
Predicting Reaction Mechanisms from Spectroscopic Data pipeline.

Directories created:
  - src/
  - tests/
  - specs/001-predicting-reaction-mechanisms/
  - data/
  - state/projects/

The script is safe to run multiple times; existing directories are left
untouched. It logs its actions using the project's logging utilities.
"""

import sys
from pathlib import Path

from llmxive_toolkit import paths, get_logger

# Obtain a logger for this script
log = get_logger(__name__)

# List of directories (relative to the project root) to create
DIRS_TO_CREATE = [
    "src",
    "tests",
    "specs/001-predicting-reaction-mechanisms",
    "data",
    "state/projects",
]


def create_directory(relative_path: str) -> Path:
    """
    Ensure a directory exists, creating it if necessary.

    Args:
        relative_path: Path relative to the project root.

    Returns:
        The absolute Path object for the created (or existing) directory.
    """
    # Use the llmxive toolkit to resolve the path; this also creates parent
    # directories when we call mkdir.
    dir_path = paths.path(relative_path)
    if not dir_path.exists():
        try:
            dir_path.mkdir(parents=True, exist_ok=True)
            log.info(f"Created directory: {dir_path}")
        except Exception as exc:
            log.error(f"Failed to create directory {dir_path}: {exc}")
            raise
    else:
        log.debug(f"Directory already exists: {dir_path}")
    return dir_path


def main() -> None:
    """
    Entry point: iterate over the required directories and create them.
    """
    log.info("Starting project directory structure creation.")
    for rel_dir in DIRS_TO_CREATE:
        create_directory(rel_dir)
    log.info("All required directories are now present.")


if __name__ == "__main__":
    # When the script is executed directly, run the main routine.
    # This allows `python code/scripts/create_project_structure.py` to work.
    try:
        main()
    except Exception as e:
        log.error(f"Directory creation failed: {e}")
        sys.exit(1)