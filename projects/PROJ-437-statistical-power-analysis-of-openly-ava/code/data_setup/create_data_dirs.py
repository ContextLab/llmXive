"""
Module to create the required data directory structure for the project.

This script ensures that the following directories exist:
- data/
- data/raw/
- data/derived/
- data/aggregated/

It is idempotent: running it multiple times will not cause errors if the 
directories already exist.
"""
import os
import sys
from pathlib import Path


def create_data_directories(base_dir: Path = None) -> None:
    """
    Create the required data directory hierarchy.
    
    Args:
        base_dir: The root directory of the project. Defaults to the parent 
                  of this file's location (assuming standard project structure).
    """
    if base_dir is None:
        # Default to the project root (parent of code/data_setup/)
        base_dir = Path(__file__).resolve().parent.parent.parent
    
    data_root = base_dir / "data"
    subdirs = ["raw", "derived", "aggregated"]
    
    for subdir in subdirs:
        target_path = data_root / subdir
        try:
            target_path.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {target_path}")
        except PermissionError:
            print(f"Error: Permission denied when creating {target_path}", file=sys.stderr)
            raise
        except Exception as e:
            print(f"Error creating directory {target_path}: {e}", file=sys.stderr)
            raise


def main() -> None:
    """Entry point for the script."""
    print("Starting data directory creation...")
    create_data_directories()
    print("Data directory creation complete.")


if __name__ == "__main__":
    main()
