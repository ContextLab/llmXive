"""
Task T004: Setup data directory structure.

Creates the required directory hierarchy for the project's data storage:
- data/raw: For original, unmodified data downloads
- data/processed: For cleaned, transformed, and model-ready data
- data/interim: For intermediate data states during processing pipelines

Creates .gitkeep files in each directory to ensure they are tracked by git
even if they are empty.
"""
import os
from pathlib import Path

def setup_data_directories():
    """Create the project data directory structure."""
    # Define the base project root (assumed to be the parent of 'code')
    # Since this script lives in 'code/', we go up one level to find 'data/'
    project_root = Path(__file__).resolve().parent.parent
    data_base = project_root / "data"

    # Define the required subdirectories
    directories = [
        data_base / "raw",
        data_base / "processed",
        data_base / "interim"
    ]

    created_dirs = []
    for directory in directories:
        if not directory.exists():
            directory.mkdir(parents=True, exist_ok=True)
            created_dirs.append(str(directory.relative_to(project_root)))
            print(f"Created directory: {directory.relative_to(project_root)}")
        else:
            print(f"Directory already exists: {directory.relative_to(project_root)}")

        # Create .gitkeep file to ensure directory is tracked by git
        gitkeep_path = directory / ".gitkeep"
        if not gitkeep_path.exists():
            gitkeep_path.touch()
            print(f"Created .gitkeep in: {directory.relative_to(project_root)}")
        else:
            print(f".gitkeep already exists in: {directory.relative_to(project_root)}")

    return created_dirs

def main():
    """Entry point for the script."""
    print("Setting up data directory structure...")
    try:
        created = setup_data_directories()
        print(f"\nSuccessfully set up {len(created)} directories.")
        print("Data structure is ready for use.")
    except Exception as e:
        print(f"Error during setup: {e}")
        raise

if __name__ == "__main__":
    main()