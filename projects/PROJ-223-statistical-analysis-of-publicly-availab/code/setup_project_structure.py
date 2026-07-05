"""
Setup script to create the project directory structure for the
Statistical Analysis of Publicly Available Traffic Accident Data project.

This script creates the following directories relative to the project root:
- code/
- data/raw/
- data/processed/
- output/
- tests/
- docs/
- state/

It also creates a .gitkeep file in each directory to ensure they are
tracked by version control even when empty.
"""
import os
from pathlib import Path

def create_project_structure():
    """Create the project directory structure."""
    # Define the directories to create relative to the project root
    directories = [
        "code",
        "data/raw",
        "data/processed",
        "output",
        "tests",
        "docs",
        "state"
    ]
    
    # Get the project root (current working directory)
    project_root = Path.cwd()
    
    print(f"Creating project structure in: {project_root}")
    
    created_dirs = []
    for dir_path in directories:
        full_path = project_root / dir_path
        
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            created_dirs.append(str(full_path))
            print(f"  Created: {full_path}")
        else:
            print(f"  Exists:  {full_path}")
        
        # Create .gitkeep to ensure directory is tracked by git
        gitkeep_path = full_path / ".gitkeep"
        if not gitkeep_path.exists():
            gitkeep_path.write_text("# Keep this directory in version control\n")
            print(f"  Updated: {gitkeep_path}")
    
    print(f"\nProject structure setup complete. Created {len(created_dirs)} directories.")
    return len(created_dirs)

if __name__ == "__main__":
    create_project_structure()