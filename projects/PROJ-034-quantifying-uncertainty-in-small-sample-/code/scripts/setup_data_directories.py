"""
Script to create the required data directory structure for the project.
Creates data/raw, data/simulated, and data/results directories with .gitkeep files.
"""
import os
import sys
from pathlib import Path


def create_directories():
    """Create the data directory structure with .gitkeep files."""
    # Define the base data directory relative to the project root
    # Assuming this script is run from the project root or code/scripts
    base_path = Path(__file__).resolve().parent.parent.parent
    data_root = base_path / "data"

    directories = [
        "raw",
        "simulated",
        "results"
    ]

    created_paths = []

    for dir_name in directories:
        dir_path = data_root / dir_name
        dir_path.mkdir(parents=True, exist_ok=True)
        
        # Create .gitkeep file to ensure directory is tracked by git
        gitkeep_path = dir_path / ".gitkeep"
        gitkeep_path.touch(exist_ok=True)
        
        created_paths.append(str(gitkeep_path))
        print(f"Created: {gitkeep_path}")

    return created_paths


def main():
    """Main entry point."""
    print("Setting up data directory structure...")
    try:
        created = create_directories()
        print(f"\nSuccessfully created {len(created)} directories with .gitkeep files.")
        return 0
    except Exception as e:
        print(f"Error creating directories: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
