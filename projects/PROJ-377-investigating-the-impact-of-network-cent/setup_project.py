"""
Script to initialize the project directory structure for PROJ-377.
Creates the required subdirectories under the project root.
"""
import os
from pathlib import Path

def setup_project_structure():
    """Create the project directory tree."""
    project_root = Path(__file__).parent
    
    # Define the required subdirectories
    subdirs = [
        "code",
        "data",
        "tests",
        "state"
    ]
    
    # Create directories and .gitkeep files
    for subdir in subdirs:
        dir_path = project_root / subdir
        dir_path.mkdir(parents=True, exist_ok=True)
        
        # Create .gitkeep to ensure empty directories are tracked by git
        gitkeep_path = dir_path / ".gitkeep"
        if not gitkeep_path.exists():
            gitkeep_path.write_text("# Placeholder to ensure directory exists in git\n")
            print(f"Created: {gitkeep_path}")
    
    print(f"Project structure initialized at: {project_root}")

if __name__ == "__main__":
    setup_project_structure()