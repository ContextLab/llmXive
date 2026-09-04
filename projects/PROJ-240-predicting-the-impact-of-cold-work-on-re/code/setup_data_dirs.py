"""
Setup script to create required data subdirectories for the project.
Creates: data/raw, data/processed, data/split
"""
import os
from pathlib import Path

def main():
    """Create the required data directory structure."""
    # Define the base project root
    # Assuming the script is run from the project root or the code directory
    # We use the parent of this file's directory to find the project root
    current_dir = Path(__file__).resolve().parent
    project_root = current_dir.parent

    data_root = project_root / "data"

    # Define required subdirectories
    required_dirs = [
        data_root / "raw",
        data_root / "processed",
        data_root / "split"
    ]

    # Create directories if they don't exist
    created_count = 0
    for dir_path in required_dirs:
        if not dir_path.exists():
            dir_path.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {dir_path}")
            created_count += 1
        else:
            print(f"Directory already exists: {dir_path}")

    print(f"Data directory setup complete. {created_count} new directories created.")
    return 0

if __name__ == "__main__":
    exit(main())
