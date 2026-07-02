import os
import sys
from pathlib import Path

def create_data_directories():
    """
    Creates the required directory structure for the fMRI analysis project.
    This includes data subdirectories and code subdirectories that may be
    missing from previous setup steps.
    """
    base_dir = Path(__file__).resolve().parent.parent
    data_dir = base_dir / "data"
    code_dir = base_dir / "code"

    # Data directories required by T004
    data_subdirs = [
        "raw-fmri",
        "processed-fmri",
        "behavioral",
        "results"
    ]

    # Code directories required by T004 (some may exist from T001c/T003, but ensure they exist)
    code_subdirs = [
        "manipulation",
        "utils"
    ]

    created_count = 0

    for subdir in data_subdirs:
        target_path = data_dir / subdir
        if not target_path.exists():
            target_path.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {target_path}")
            created_count += 1
        else:
            print(f"Directory already exists: {target_path}")

    for subdir in code_subdirs:
        target_path = code_dir / subdir
        if not target_path.exists():
            target_path.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {target_path}")
            created_count += 1
        else:
            print(f"Directory already exists: {target_path}")

    # Create placeholder .gitkeep files to ensure directories are tracked by git
    for subdir in data_subdirs:
        target_path = data_dir / subdir / ".gitkeep"
        target_path.touch()

    for subdir in code_subdirs:
        target_path = code_dir / subdir / ".gitkeep"
        target_path.touch()

    return created_count

def main():
    """Entry point for script execution."""
    print("Setting up project directory structure...")
    count = create_data_directories()
    print(f"Successfully created/verified {count} new directories.")
    print("Directory structure setup complete.")

if __name__ == "__main__":
    main()