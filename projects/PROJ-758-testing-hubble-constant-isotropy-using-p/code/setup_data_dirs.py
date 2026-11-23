"""
Script to initialize the data directory structure for the Hubble Constant Isotropy project.

This script creates the required directory hierarchy under the 'data/' folder:
- data/raw/: For raw, unmodified data downloads (e.g., from Zenodo)
- data/processed/: For cleaned and transformed data ready for analysis
- data/results/: For final analysis outputs, metrics, and reports

Usage:
    python code/setup_data_dirs.py
"""
import os
import sys
from pathlib import Path

def main():
    """Create the standard data directory structure."""
    # Determine the project root (assuming script is in code/)
    script_dir = Path(__file__).resolve().parent
    project_root = script_dir.parent
    
    data_root = project_root / "data"
    subdirs = ["raw", "processed", "results"]
    
    created_count = 0
    
    for subdir_name in subdirs:
        target_path = data_root / subdir_name
        
        if not target_path.exists():
            target_path.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {target_path}")
            created_count += 1
        else:
            print(f"Directory already exists: {target_path}")
    
    # Create a .gitkeep in each to ensure they are tracked by git even if empty
    for subdir_name in subdirs:
        keep_file = data_root / subdir_name / ".gitkeep"
        if not keep_file.exists():
            keep_file.touch()
            print(f"Created .gitkeep in: {keep_file}")
            created_count += 1
    
    print(f"\nData directory structure initialized successfully.")
    print(f"Root: {data_root}")
    print(f"Directories created/updated: {created_count}")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())