"""
Data Directory Setup Script.

Creates the required directory structure for the molecular chirality project
and places .gitkeep files to ensure the directories are tracked by git.

This script fulfills task T004: Setup data directory structure.
"""
import os
from pathlib import Path


def setup_data_directories():
    """
    Create the standard project data directory structure.

    Creates the following directories relative to the project root:
    - data/raw: For original, unprocessed data sources
    - data/processed: For cleaned, aggregated, and analysis-ready data
    - data/interim: For intermediate data transformations

    Also ensures .gitkeep files exist in each directory to preserve
    directory structure in version control.
    """
    # Determine project root based on script location
    # Assuming this script is in code/04_setup_data_dirs.py
    script_dir = Path(__file__).resolve().parent
    project_root = script_dir.parent

    # Define data directories
    data_dirs = [
        project_root / "data" / "raw",
        project_root / "data" / "processed",
        project_root / "data" / "interim",
        # Also ensure logs directory exists for T008
        project_root / "data" / "logs",
        # Ensure figures directory exists for output plots
        project_root / "figures",
    ]

    created_count = 0
    for dir_path in data_dirs:
        if not dir_path.exists():
            dir_path.mkdir(parents=True, exist_ok=True)
            created_count += 1
            print(f"Created directory: {dir_path}")
        else:
            print(f"Directory already exists: {dir_path}")

        # Create .gitkeep file to ensure directory is tracked
        gitkeep_path = dir_path / ".gitkeep"
        if not gitkeep_path.exists():
            gitkeep_path.touch()
            print(f"Created .gitkeep in: {dir_path}")
        else:
            print(f".gitkeep already exists in: {dir_path}")

    print(f"\nSetup complete. Created/verified {created_count} new directories.")
    return True


def main():
    """Entry point for the script."""
    print("Starting data directory setup...")
    success = setup_data_directories()
    if success:
        print("Data directory structure is ready.")
    else:
        print("Failed to set up data directory structure.")
        exit(1)


if __name__ == "__main__":
    main()