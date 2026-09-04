"""
Data Directory Setup Module.

This module provides functionality to initialize the required directory
structure for the project's data management system. It ensures that
the `data/` directory and its subdirectories (`raw/`, `processed/`,
`contracts/`) exist on the filesystem.

This satisfies task T004: Setup `data/` directory structure.
"""
import os
from pathlib import Path


def setup_data_directories() -> None:
    """
    Create the required data directory structure if it does not already exist.

    This function creates the following directory hierarchy relative to
    the project root:
    - data/
        - raw/          (For unmodified source data)
        - processed/    (For cleaned/transformed data)
        - contracts/    (For data schema contracts and validation rules)

    The function is idempotent; running it multiple times will not raise
    errors if the directories already exist.

    Side Effects:
        Creates directories on the local filesystem.
    """
    # Define the base project root. Assuming this script is in code/,
    # the project root is the parent of code/.
    # However, to be robust when run as a module or script, we look for
    # the 'data' directory relative to the current working directory
    # or a standard project root detection.
    # Given the constraint "Stay inside the project tree", we assume
    # the script is run from the project root or code is structured such
    # that 'data' is a sibling to 'code'.
    
    # Strategy: Look for 'data' in the current working directory.
    # If not found, and 'code' exists in cwd, assume cwd is project root.
    
    current_dir = Path.cwd()
    data_root = current_dir / "data"
    
    subdirectories = ["raw", "processed", "contracts"]
    
    for subdir_name in subdirectories:
        subdir_path = data_root / subdir_name
        try:
            subdir_path.mkdir(parents=True, exist_ok=True)
            # Optionally verify it's a directory
            if not subdir_path.is_dir():
                raise RuntimeError(f"Failed to create directory: {subdir_path}")
        except PermissionError:
            raise RuntimeError(f"Permission denied when creating directory: {subdir_path}")
        except OSError as e:
            raise RuntimeError(f"OS error while creating directory {subdir_path}: {e}")

    # Log the successful creation (using standard print for setup scripts
    # as logging infrastructure T008 is not yet fully active, 
    # though utils.py has get_logger, we keep this simple for setup)
    print(f"Data directory structure verified/created at: {data_root}")
    for subdir in subdirectories:
        print(f"  - {data_root / subdir}")


if __name__ == "__main__":
    setup_data_directories()