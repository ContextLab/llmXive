"""
Setup script to initialize the required data directory structure.

This script creates the following directories relative to the project root:
- data/raw/
- data/processed/
- data/processed/results/

It ensures that all necessary folders exist before data ingestion or 
processing tasks begin.
"""
import os
from pathlib import Path
import sys

# Add the project root to the path to allow imports if needed, 
# though this script primarily uses stdlib.
# Assuming the script is run from the project root or code/ directory.

def get_project_root() -> Path:
    """Determine the project root directory."""
    # If running as `python code/src/setup_data_structure.py` from root
    # or `python src/setup_data_structure.py` from code/
    current_file = Path(__file__).resolve()
    
    # Check if we are in code/src/
    if current_file.parent.name == "src" and current_file.parent.parent.name == "code":
        return current_file.parent.parent.parent
    
    # Fallback: assume current working directory is root
    return Path.cwd()

def setup_directories(root_dir: Path) -> None:
    """Create the required data directory structure."""
    data_dir = root_dir / "data"
    raw_dir = data_dir / "raw"
    processed_dir = data_dir / "processed"
    results_dir = processed_dir / "results"
    
    directories = [
        data_dir,
        raw_dir,
        processed_dir,
        results_dir
    ]
    
    created_count = 0
    for directory in directories:
        if not directory.exists():
            directory.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {directory}")
            created_count += 1
        else:
            print(f"Directory already exists: {directory}")
    
    if created_count == 0:
        print("All required directories already exist.")
    else:
        print(f"Successfully created {created_count} directory/directories.")

def main() -> None:
    """Main entry point for the script."""
    root = get_project_root()
    print(f"Project root detected at: {root}")
    setup_directories(root)

if __name__ == "__main__":
    main()