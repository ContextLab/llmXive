"""
Setup script for PROJ-357: The Impact of Visual Crowding on Facial Emotion Recognition Accuracy.

This script creates the required directory structure for the project:
- code/
- data/
- tests/
- artifacts/
- state/projects/

It also initializes a .gitkeep file in each directory to ensure they are tracked
by version control even if empty.
"""
import os
from pathlib import Path

def setup_project_structure():
    """Create the project directory structure."""
    # Define the base project directory
    base_dir = Path("projects/PROJ-357-the-impact-of-visual-crowding-on-facial-")
    
    # Define subdirectories to create
    subdirectories = [
        "code",
        "data",
        "tests",
        "artifacts",
        "state/projects"
    ]
    
    # Create the base directory and subdirectories
    base_dir.mkdir(parents=True, exist_ok=True)
    
    created_paths = []
    for subdir in subdirectories:
        full_path = base_dir / subdir
        full_path.mkdir(parents=True, exist_ok=True)
        created_paths.append(str(full_path))
        
        # Create a .gitkeep file to ensure the directory is tracked by git
        gitkeep_path = full_path / ".gitkeep"
        gitkeep_path.touch()
    
    print(f"Project structure created successfully at: {base_dir}")
    print(f"Created directories:")
    for path in created_paths:
        print(f"  - {path}")
    
    return True

if __name__ == "__main__":
    setup_project_structure()