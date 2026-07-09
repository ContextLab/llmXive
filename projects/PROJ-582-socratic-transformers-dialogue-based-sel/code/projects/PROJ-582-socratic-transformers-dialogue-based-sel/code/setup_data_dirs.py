"""
Setup script for T004: Create data directory structure and .gitkeep files.

This script creates the required directory tree for the project's data storage:
- data/raw/         : For raw downloaded datasets (e.g., GSM8K, MATH)
- data/processed/   : For extracted and cleaned data tuples
- data/results/     : For model outputs, logs, and evaluation metrics

It also ensures .gitkeep files exist in each directory to preserve them in git.
"""
import os
import sys
from pathlib import Path

def main():
    # Determine the project root relative to this script's location
    # Script is at: projects/PROJ-582-socratic-transformers-dialogue-based-sel/code/setup_data_dirs.py
    # We want to create directories relative to the project root:
    # projects/PROJ-582-socratic-transformers-dialogue-based-sel/
    
    script_path = Path(__file__).resolve()
    project_root = script_path.parent.parent  # Goes up two levels from code/
    
    data_root = project_root / "data"
    subdirs = ["raw", "processed", "results"]
    
    print(f"Project root: {project_root}")
    print(f"Creating data structure under: {data_root}")
    
    created_dirs = []
    for subdir in subdirs:
        target_dir = data_root / subdir
        if not target_dir.exists():
            target_dir.mkdir(parents=True, exist_ok=True)
            created_dirs.append(target_dir)
            print(f"  Created: {target_dir}")
        else:
            print(f"  Exists:  {target_dir}")
        
        # Ensure .gitkeep exists
        gitkeep = target_dir / ".gitkeep"
        if not gitkeep.exists():
            gitkeep.touch()
            print(f"  Created: {gitkeep}")
        else:
            print(f"  Exists:  {gitkeep}")
    
    if created_dirs:
        print(f"\nSuccessfully created {len(created_dirs)} directories.")
    else:
        print("\nAll directories already existed.")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())