"""
Script to create the state directories required for the project.
Follows Constitution Principle III and FR-001.
"""
import os
import sys
from pathlib import Path

# Project root is assumed to be the parent of this script's directory
PROJECT_ROOT = Path(__file__).parent.parent

# The specific state directory path for this project
STATE_DIR_PATH = PROJECT_ROOT / "state" / "projects" / "PROJ-560-embodied-curriculum-learning-physical-si"

def create_directory(path: Path) -> bool:
    """
    Creates a directory if it does not exist.
    Returns True if successful, False otherwise.
    """
    try:
        path.mkdir(parents=True, exist_ok=True)
        print(f"Created directory: {path}")
        return True
    except OSError as e:
        print(f"Error creating directory {path}: {e}", file=sys.stderr)
        return False

def main():
    """
    Main entry point to create the state directory structure.
    """
    print(f"Project Root: {PROJECT_ROOT}")
    print(f"Target State Directory: {STATE_DIR_PATH}")

    if create_directory(STATE_DIR_PATH):
        print("State directory setup complete.")
        sys.exit(0)
    else:
        print("Failed to create state directory.", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()