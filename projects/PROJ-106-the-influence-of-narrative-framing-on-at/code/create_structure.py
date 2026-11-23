"""
Script to create the required project directory structure.
This script ensures all necessary folders for the research pipeline exist.
"""
import os
from pathlib import Path

def main():
    root = Path(".")
    
    # Define the required directory structure based on tasks.md
    directories = [
        "code",
        "code/utils",
        "data",
        "data/raw",
        "data/processed",
        "data/stimuli",
        "data/ethics",
        "tests",
        "specs"
    ]

    created_count = 0
    for dir_path in directories:
        full_path = root / dir_path
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {full_path}")
            created_count += 1
        else:
            print(f"Directory exists: {full_path}")

    # Create .gitkeep files to ensure directories are tracked in git
    keep_files = []
    for dir_path in directories:
        full_path = root / dir_path
        keep_file = full_path / ".gitkeep"
        if not keep_file.exists():
            keep_file.touch()
            keep_files.append(keep_file)
            print(f"Created .gitkeep: {keep_file}")

    print(f"\nStructure setup complete. Created {created_count} directories and {len(keep_files)} keep files.")

if __name__ == "__main__":
    main()
