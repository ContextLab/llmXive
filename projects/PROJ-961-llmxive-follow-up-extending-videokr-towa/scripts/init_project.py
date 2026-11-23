"""
Project Initialization Script for llmXive Automated Science Pipeline.

This script creates the required directory structure and .gitkeep files
for the PROJ-961-llmxive-follow-up-extending-videokr-towa project.

Directories created:
- code/
- tests/
- data/
- data/raw/
- data/processed/
- code/ingest/
- code/analysis/
- code/utils/
- tests/unit/
- tests/integration/
"""

import os
import sys
from pathlib import Path


def create_directory(path: Path) -> None:
    """Create a directory if it does not exist.

    Args:
        path: The Path object representing the directory to create.

    Raises:
        OSError: If the directory cannot be created.
    """
    try:
        path.mkdir(parents=True, exist_ok=True)
        print(f"Created directory: {path}")
    except OSError as e:
        print(f"Error creating directory {path}: {e}")
        raise


def create_gitkeep(path: Path) -> None:
    """Create a .gitkeep file in the specified directory.

    Args:
        path: The Path object representing the directory.
    """
    gitkeep_file = path / ".gitkeep"
    try:
        gitkeep_file.touch(exist_ok=True)
        print(f"Created .gitkeep in: {path}")
    except OSError as e:
        print(f"Error creating .gitkeep in {path}: {e}")
        raise


def verify_directory(path: Path) -> bool:
    """Verify that a directory exists.

    Args:
        path: The Path object representing the directory to verify.

    Returns:
        True if the directory exists, False otherwise.
    """
    return os.path.exists(path) and os.path.isdir(path)


def ensure_directory_structure(base_path: Path) -> None:
    """Ensure the complete directory structure exists.

    Args:
        base_path: The base path where the structure should be created.

    Raises:
        RuntimeError: If any directory creation or verification fails.
    """
    # Define the required directories relative to the base path
    required_dirs = [
        "code",
        "tests",
        "data",
        "data/raw",
        "data/processed",
        "code/ingest",
        "code/analysis",
        "code/utils",
        "tests/unit",
        "tests/integration",
    ]

    # Create all directories
    for dir_name in required_dirs:
        full_path = base_path / dir_name
        create_directory(full_path)
        create_gitkeep(full_path)

    # Verify all directories exist
    print("\nVerifying directory structure...")
    all_verified = True
    for dir_name in required_dirs:
        full_path = base_path / dir_name
        if not verify_directory(full_path):
            print(f"ERROR: Directory missing: {full_path}")
            all_verified = False

    if not all_verified:
        raise RuntimeError("Directory structure verification failed. Some directories are missing.")

    print("All directories verified successfully.")


def main() -> int:
    """Main entry point for the script.

    Returns:
        0 on success, 1 on failure.
    """
    # Determine the base path (project root)
    # The script is expected to be run from the project root
    base_path = Path.cwd()

    print(f"Initializing project structure in: {base_path}")
    print("-" * 50)

    try:
        ensure_directory_structure(base_path)
        print("-" * 50)
        print("Project structure initialization completed successfully.")
        return 0
    except Exception as e:
        print(f"Initialization failed: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())