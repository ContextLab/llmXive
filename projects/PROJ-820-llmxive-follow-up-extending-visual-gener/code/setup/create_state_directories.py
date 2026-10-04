"""
Module to create the state directory structure for the llmXive project.
Specifically creates the 'state/projects' directory and its parents if they do not exist.
"""
import os
import sys
from pathlib import Path

def create_directory(path: Path) -> bool:
    """
    Creates a directory if it does not exist.

    Args:
        path: The Path object representing the directory to create.

    Returns:
        True if the directory was created or already exists, False otherwise.
    """
    try:
        path.mkdir(parents=True, exist_ok=True)
        # Verify existence to ensure it wasn't a permission issue that mkdir silently ignored (rare)
        if not path.exists():
            return False
        return True
    except OSError as e:
        print(f"Error creating directory {path}: {e}", file=sys.stderr)
        return False

def main():
    """
    Main entry point to create the state/projects directory structure.
    """
    project_root = Path(__file__).resolve().parent.parent.parent
    state_dir = project_root / "state"
    projects_dir = state_dir / "projects"

    print(f"Ensuring directory structure exists: {projects_dir}")

    if create_directory(projects_dir):
        print(f"Successfully created or verified directory: {projects_dir}")
        return 0
    else:
        print(f"Failed to create directory: {projects_dir}", file=sys.stderr)
        return 1

if __name__ == "__main__":
    sys.exit(main())
