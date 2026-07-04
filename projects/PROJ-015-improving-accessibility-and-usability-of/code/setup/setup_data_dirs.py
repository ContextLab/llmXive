"""
Setup script to initialize the project's data directory structure.

Creates:
  - data/raw/ (immutable raw data storage)
  - data/processed/ (derived/analyzed data storage)

Also creates a .gitkeep file in each to ensure they are tracked by git.
"""
import os
import stat
import sys
from pathlib import Path


def get_project_root() -> Path:
    """
    Determine the project root directory.
    Assumes this script is located at code/setup/setup_data_dirs.py.
    """
    current_file = Path(__file__).resolve()
    # Navigate up two levels: code/setup -> code -> project_root
    return current_file.parent.parent.parent


def ensure_directory(dir_path: Path, immutable: bool = False) -> None:
    """
    Ensure a directory exists. If it doesn't, create it and a .gitkeep file.
    
    Args:
        dir_path: The path to the directory to create.
        immutable: If True, sets read-only permissions on the directory 
                   (simulating immutability for raw data).
    """
    if not dir_path.exists():
        dir_path.mkdir(parents=True, exist_ok=True)
        gitkeep_path = dir_path / ".gitkeep"
        gitkeep_path.touch()
        print(f"Created directory: {dir_path}")
        
        if immutable:
            # On Unix-like systems, set read-only permissions
            # Note: On Windows, this logic is less straightforward but 
            # the concept of immutability is primarily logical here.
            try:
                current_perms = os.stat(dir_path).st_mode
                # Remove write permissions for owner, group, and others
                os.chmod(dir_path, current_perms & ~stat.S_IWUSR & ~stat.S_IWGRP & ~stat.S_IWOTH)
                print(f"Set read-only permissions on: {dir_path}")
            except OSError as e:
                print(f"Warning: Could not set immutable permissions on {dir_path}: {e}")
    else:
        print(f"Directory already exists: {dir_path}")


def main() -> None:
    """Main entry point to setup data directories."""
    root = get_project_root()
    data_dir = root / "data"
    raw_dir = data_dir / "raw"
    processed_dir = data_dir / "processed"

    print(f"Project root detected at: {root}")
    print(f"Setting up data directories under: {data_dir}")

    # Create raw directory (immutable)
    ensure_directory(raw_dir, immutable=True)
    
    # Create processed directory (mutable)
    ensure_directory(processed_dir, immutable=False)

    print("Data directory structure setup complete.")


if __name__ == "__main__":
    main()