"""
Script to initialize the root project directory structure for llmXive PROJ-383.

Creates the required directories:
- code/
- data/
- tests/

And initializes subdirectories within data/ as per T006 requirements:
- data/raw_fmri
- data/raw_behavior
- data/processed
- data/results
"""
import os
from pathlib import Path

def main():
    root = Path(__file__).resolve().parent.parent
    
    # Define root directories required by T001a
    root_dirs = [
        root / "code",
        root / "data",
        root / "tests"
    ]
    
    # Define subdirectories required by T006 (data structure)
    data_subdirs = [
        root / "data" / "raw_fmri",
        root / "data" / "raw_behavior",
        root / "data" / "processed",
        root / "data" / "results"
    ]
    
    all_dirs = root_dirs + data_subdirs
    
    created_count = 0
    for directory in all_dirs:
        if not directory.exists():
            directory.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {directory.relative_to(root)}")
            created_count += 1
        else:
            print(f"Directory already exists: {directory.relative_to(root)}")
    
    # Create .gitkeep files to ensure directories are tracked by git
    gitkeep_dirs = [root / "code", root / "data", root / "tests"]
    for directory in gitkeep_dirs:
        gitkeep = directory / ".gitkeep"
        if not gitkeep.exists():
            gitkeep.touch()
            print(f"Created .gitkeep in: {directory.relative_to(root)}")
    
    print(f"\nInitialization complete. {created_count} new directories created.")
    print(f"Project structure ready at: {root}")

if __name__ == "__main__":
    main()