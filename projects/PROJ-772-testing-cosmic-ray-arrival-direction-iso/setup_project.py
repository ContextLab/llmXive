"""
Script to initialize the project directory structure for PROJ-772.
This script creates the required directories and placeholder files.
"""
import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent
SUBDIRS = ["code", "data", "tests", "state"]
PLACEHOLDER_FILES = [
    ("data", ".gitkeep"),
    ("state", ".gitkeep"),
    ("state/projects", ".gitkeep"),
]

def main():
    print(f"Initializing project structure at: {PROJECT_ROOT}")

    # Create root subdirectories
    for subdir in SUBDIRS:
        dir_path = PROJECT_ROOT / subdir
        dir_path.mkdir(exist_ok=True)
        print(f"  Created: {dir_path}")

    # Create placeholder .gitkeep files
    for parent, filename in PLACEHOLDER_FILES:
        file_path = PROJECT_ROOT / parent / filename
        # Ensure parent directory exists
        file_path.parent.mkdir(parents=True, exist_ok=True)
        if not file_path.exists():
            file_path.touch()
            print(f"  Created: {file_path}")
        else:
            print(f"  Exists: {file_path}")

    print("Project structure initialization complete.")

if __name__ == "__main__":
    main()