"""
Utility module for ensuring project directory structures exist.

Implements robust 'mkdir -p' logic for data directories required by the pipeline.
"""
from pathlib import Path
import os
import sys

# Define the project root relative to this file's location (code/utils/)
# Assuming the project structure is:
# code/
#   utils/
#     directories.py
# data/
#   raw/
#   processed/
#   results/
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

# Directories to ensure exist
DATA_DIRS = [
    "data/raw",
    "data/processed",
    "data/results",
]

def ensure_data_directories() -> list[Path]:
    """
    Creates the required data directory structure if it does not exist.
    
    Uses robust mkdir logic (parents=True, exist_ok=True) to mimic 'mkdir -p'.
    
    Returns:
        list[Path]: A list of Path objects for the directories that were ensured.
        
    Raises:
        PermissionError: If the script lacks permission to create directories.
        OSError: If any other OS-level error occurs during directory creation.
    """
    created_dirs = []
    
    for dir_rel_path in DATA_DIRS:
        full_path = _PROJECT_ROOT / dir_rel_path
        
        try:
            full_path.mkdir(parents=True, exist_ok=True)
            created_dirs.append(full_path)
        except PermissionError as e:
            raise PermissionError(
                f"Permission denied while creating directory: {full_path}. "
                "Check write permissions for the project root."
            ) from e
        except OSError as e:
            raise OSError(f"Failed to create directory {full_path}: {e}") from e
    
    return created_dirs

def main() -> None:
    """
    CLI entry point to ensure data directories exist.
    
    Prints the paths of created/verified directories to stdout.
    """
    try:
        dirs = ensure_data_directories()
        print("Ensured existence of the following directories:")
        for d in dirs:
            print(f"  - {d}")
        print("Success.")
    except (PermissionError, OSError) as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
