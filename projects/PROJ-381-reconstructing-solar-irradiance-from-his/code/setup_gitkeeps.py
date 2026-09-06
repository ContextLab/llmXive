"""
Script to create .gitkeep files in data directories to ensure they are tracked by Git.
This satisfies task T001c.
"""
import os
from pathlib import Path

def main():
    """Create .gitkeep files in data/raw and data/processed."""
    # Define the relative paths for the data directories
    data_dirs = [
        "data/raw",
        "data/processed"
    ]

    project_root = Path(__file__).parent.parent
    
    created_files = []
    
    for dir_path in data_dirs:
        full_path = project_root / dir_path
        
        # Create the directory if it doesn't exist (defensive, though T001a should have done this)
        full_path.mkdir(parents=True, exist_ok=True)
        
        gitkeep_path = full_path / ".gitkeep"
        
        # Create the .gitkeep file if it doesn't exist
        if not gitkeep_path.exists():
            gitkeep_path.touch()
            created_files.append(str(gitkeep_path))
            print(f"Created: {gitkeep_path}")
        else:
            print(f"Already exists: {gitkeep_path}")
    
    if not created_files:
        print("All .gitkeep files already present.")
    else:
        print(f"Successfully created {len(created_files)} .gitkeep file(s).")

if __name__ == "__main__":
    main()
