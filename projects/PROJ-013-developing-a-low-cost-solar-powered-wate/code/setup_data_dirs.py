"""
Setup script for T004: Initialize data directory structure.

Creates the required directory tree for the solar purification project:
- data/raw/          : Raw data sources (API downloads, scraped files)
- data/processed/    : Cleaned/transformed data ready for analysis
- data/plots/        : Generated visualization artifacts
"""
import os
import sys
from pathlib import Path

def main():
    # Define the project root (parent of the code/ directory)
    script_path = Path(__file__).resolve()
    project_root = script_path.parent.parent
    
    # Define the required directories relative to project root
    base_data_dir = project_root / "data"
    directories = [
        base_data_dir / "raw",
        base_data_dir / "processed",
        base_data_dir / "plots",
    ]
    
    created_count = 0
    skipped_count = 0
    
    print(f"Initializing data directories in: {base_data_dir}")
    
    for directory in directories:
        if directory.exists():
            print(f"  [SKIP] {directory} already exists.")
            skipped_count += 1
        else:
            directory.mkdir(parents=True, exist_ok=True)
            print(f"  [CREATED] {directory}")
            created_count += 1
    
    # Create a .gitkeep file in each to ensure they are tracked by git
    for directory in directories:
        keep_file = directory / ".gitkeep"
        if not keep_file.exists():
            keep_file.write_text("# Keep this directory in git\n")
            print(f"  [ADDED] .gitkeep in {directory}")
    
    print(f"\nSummary: {created_count} created, {skipped_count} skipped.")
    return 0

if __name__ == "__main__":
    sys.exit(main())