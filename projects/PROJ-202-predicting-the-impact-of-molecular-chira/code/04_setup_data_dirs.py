"""
Task T004: Setup data directory structure.

Creates the required directory hierarchy for the project's data artifacts:
- data/raw: For raw, unprocessed data fetched from external sources.
- data/processed: For cleaned, transformed, and analysis-ready data.
- data/interim: For intermediate data files generated during processing steps.

This script ensures that all necessary directories exist and contains
empty .gitkeep files to preserve the directory structure in version control.
"""

import os
from pathlib import Path


def setup_data_directories():
    """
    Create the standard data directory structure and .gitkeep files.

    Directories created relative to the project root:
    - data/raw
    - data/processed
    - data/interim

    Returns:
        bool: True if all directories were created/successfully verified.
    """
    project_root = Path(__file__).resolve().parent.parent
    data_root = project_root / "data"

    directories = [
        data_root / "raw",
        data_root / "processed",
        data_root / "interim",
    ]

    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)
        gitkeep_path = directory / ".gitkeep"
        if not gitkeep_path.exists():
            gitkeep_path.touch()
            print(f"Created: {gitkeep_path}")
        else:
            print(f"Already exists: {gitkeep_path}")

    return True


def main():
    """Entry point for the script."""
    print("Setting up data directory structure...")
    success = setup_data_directories()
    if success:
        print("Data directory setup complete.")
    else:
        print("Data directory setup failed.")
        exit(1)


if __name__ == "__main__":
    main()
