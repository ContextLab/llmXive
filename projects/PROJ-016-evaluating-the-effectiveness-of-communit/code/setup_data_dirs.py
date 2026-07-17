"""
Setup script for data and output directories.
Creates the required directory structure for the project.
"""
import os
import sys
from pathlib import Path

def main():
    """Create data and output directories if they don't exist."""
    # Define the project root (assuming code/ is a subdirectory)
    # We need to go up one level from code/ to find the root
    current_dir = Path(__file__).resolve().parent
    project_root = current_dir.parent

    # Define directories to create
    directories = [
        project_root / "data" / "raw",
        project_root / "data" / "processed",
        project_root / "docs" / "output",
        project_root / "logs",  # Added for logging infrastructure (T005)
    ]

    created = []
    for dir_path in directories:
        if not dir_path.exists():
            dir_path.mkdir(parents=True, exist_ok=True)
            created.append(str(dir_path.relative_to(project_root)))
            print(f"Created directory: {dir_path.relative_to(project_root)}")
        else:
            print(f"Directory already exists: {dir_path.relative_to(project_root)}")

    if created:
        print(f"\nSuccessfully created {len(created)} directory/directories.")
    else:
        print("\nAll directories already existed.")

    return 0

if __name__ == "__main__":
    sys.exit(main())
