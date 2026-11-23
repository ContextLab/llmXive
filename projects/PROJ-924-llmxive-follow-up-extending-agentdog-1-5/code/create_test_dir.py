"""
Module to create and verify the data/test directory for the project.
This task ensures the directory exists for storing test fixtures and ground truth data.
"""
import os
from pathlib import Path
from typing import Optional

from config import get_path, ensure_directories


def ensure_test_directory(base_path: Optional[Path] = None) -> Path:
    """
    Creates and verifies the existence of the data/test directory.

    Args:
        base_path: Optional base project path. If None, uses config default.

    Returns:
        Path to the created/verified directory.

    Raises:
        FileNotFoundError: If the directory cannot be created or verified.
    """
    if base_path is None:
        # Use the project root as defined in config
        project_root = get_path("project_root")
        test_dir_path = project_root / "data" / "test"
    else:
        test_dir_path = base_path / "data" / "test"

    # Ensure the directory exists
    ensure_directories([test_dir_path])

    # Verify existence
    if not test_dir_path.exists():
        raise FileNotFoundError(
            f"Failed to create or verify directory: {test_dir_path}"
        )
    if not test_dir_path.is_dir():
        raise NotADirectoryError(
            f"Path exists but is not a directory: {test_dir_path}"
        )

    return test_dir_path


def main() -> int:
    """
    Main entry point for the script.
    Creates the test directory and verifies it.

    Returns:
        0 on success, 1 on failure.
    """
    try:
        test_dir = ensure_test_directory()
        print(f"Successfully created/verified directory: {test_dir}")
        return 0
    except (FileNotFoundError, NotADirectoryError) as e:
        print(f"Error: {e}")
        return 1
    except Exception as e:
        print(f"Unexpected error: {e}")
        return 1


if __name__ == "__main__":
    import sys
    sys.exit(main())
