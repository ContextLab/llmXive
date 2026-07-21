"""
Script to create the required data directory structure.
This implements Task T005: Create data directory structure.
"""
import os
from pathlib import Path
from config import get_project_root

def create_directories():
    """Create the required data subdirectories: raw, processed, consent."""
    project_root = get_project_root()
    data_dir = project_root / "data"

    # Define the required subdirectories
    subdirs = [
        "raw",
        "processed",
        "consent"
    ]

    created_count = 0
    for subdir_name in subdirs:
        subdir_path = data_dir / subdir_name
        if not subdir_path.exists():
            subdir_path.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {subdir_path}")
            created_count += 1
        else:
            print(f"Directory already exists: {subdir_path}")

    # Create .gitkeep files to ensure directories are tracked by git
    for subdir_name in subdirs:
        keep_file = data_dir / subdir_name / ".gitkeep"
        keep_file.touch(exist_ok=True)
        print(f"Created .gitkeep in: {keep_file}")

    if created_count == 0:
        print("All required directories already exist.")
    else:
        print(f"Successfully created {created_count} directory(ies).")

    return True

def main():
    """Entry point for the script."""
    try:
        success = create_directories()
        if success:
            print("Data directory structure setup complete.")
        else:
            print("Data directory structure setup failed.")
            exit(1)
    except Exception as e:
        print(f"Error during setup: {e}")
        exit(1)

if __name__ == "__main__":
    main()