"""
Setup script to initialize the viz directory structure for the project.
Creates the viz directory and a .gitkeep file to ensure it is tracked by git.
"""
import os
import sys
from pathlib import Path

# Ensure the project root is in the path to import utils
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from utils.config import get_project_root, get_viz_dir, ensure_directories


def main():
    """
    Main entry point to initialize the viz directory.
    """
    root = get_project_root()
    viz_dir = get_viz_dir()

    print(f"Initializing viz directory at: {viz_dir}")

    # Create the directory if it doesn't exist
    ensure_directories([viz_dir])

    # Create .gitkeep file
    gitkeep_path = viz_dir / ".gitkeep"
    if not gitkeep_path.exists():
        gitkeep_path.touch()
        print(f"Created .gitkeep at: {gitkeep_path}")
    else:
        print(f".gitkeep already exists at: {gitkeep_path}")

    print("Viz directory initialization complete.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
