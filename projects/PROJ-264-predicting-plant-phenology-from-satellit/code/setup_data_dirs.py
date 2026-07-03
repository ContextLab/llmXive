"""
Script to initialize the project's data directory structure.

Creates `data/raw/` and `data/processed/` directories as required by T001c.
Also initializes a .gitkeep in each to ensure they are tracked by git.
"""
import os
import sys
from pathlib import Path

def main():
    # Define the project root relative to this script's location
    # Assuming script is in code/
    project_root = Path(__file__).parent.parent
    data_root = project_root / "data"
    
    directories = [
        data_root / "raw",
        data_root / "processed"
    ]
    
    created_dirs = []
    
    for directory in directories:
        if not directory.exists():
            directory.mkdir(parents=True, exist_ok=True)
            created_dirs.append(str(directory.relative_to(project_root)))
            
            # Create .gitkeep to ensure directory is tracked
            gitkeep = directory / ".gitkeep"
            gitkeep.write_text("# Keep directory in git\n")
            created_dirs.append(f"  - {gitkeep.relative_to(project_root)}")
        else:
            print(f"Directory already exists: {directory.relative_to(project_root)}")
    
    if created_dirs:
        print("Successfully created data directories:")
        for d in created_dirs:
            print(f"  {d}")
    else:
        print("No new directories were created.")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
