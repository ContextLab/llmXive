"""
Setup script to initialize the data directory structure for the project.
Creates raw and processed subdirectories under the data folder.
"""
import os
from pathlib import Path

def main():
    # Determine project root (assuming script is in code/)
    project_root = Path(__file__).resolve().parent.parent
    data_root = project_root / "data"

    # Define required directories
    directories = [
        data_root / "raw",
        data_root / "processed",
        data_root / "figures",
        data_root / "interim",
    ]

    created = []
    for directory in directories:
        if not directory.exists():
            directory.mkdir(parents=True, exist_ok=True)
            created.append(str(directory))
            print(f"Created directory: {directory}")
        else:
            print(f"Directory already exists: {directory}")

    if not created:
        print("All required data directories already exist.")
    else:
        print(f"Successfully created {len(created)} directory/directories.")

    # Create .gitkeep files to ensure directories are tracked by git
    for directory in directories:
        keep_file = directory / ".gitkeep"
        if not keep_file.exists():
            keep_file.write_text("# Keep this directory in git\n")
            print(f"Created .gitkeep in: {directory}")

if __name__ == "__main__":
    main()
