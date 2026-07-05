"""
Setup script for the data directory structure.

Creates the required subdirectories under 'data/' as specified in the project
implementation plan for organizing raw, preprocessed, and external datasets.

Usage:
    python code/scripts/setup_data_dirs.py
"""
import os
from pathlib import Path

def main():
    # Define the project root relative to this script's location
    # The script is at code/scripts/, so root is two levels up
    script_dir = Path(__file__).resolve().parent
    project_root = script_dir.parent.parent
    
    data_dir = project_root / "data"
    
    # Define the required subdirectories
    subdirs = [
        "raw",
        "preprocessed",
        "external"
    ]
    
    print(f"Setting up data directory structure at: {data_dir}")
    
    for subdir in subdirs:
        target_path = data_dir / subdir
        
        if target_path.exists():
            print(f"  [SKIP] {subdir}/ already exists.")
        else:
            target_path.mkdir(parents=True, exist_ok=True)
            print(f"  [CREATE] {subdir}/")
            
            # Create a .gitkeep file to ensure the directory is tracked by git
            # even if it is empty.
            gitkeep = target_path / ".gitkeep"
            with open(gitkeep, "w") as f:
                f.write("# Directory for project data\n")
            print(f"    [CREATE] {subdir}/.gitkeep")
    
    print("Data directory structure setup complete.")

if __name__ == "__main__":
    main()