"""
Setup script to initialize the notebooks directory for the project.
Creates the directory structure and a .gitkeep file to ensure
the directory is tracked by git even when empty.
"""
import os
import sys
from pathlib import Path

def main():
    """
    Initialize the notebooks directory.
    
    Creates:
    - projects/PROJ-397-predicting-avian-foraging-behavior-from-/code/notebooks/
    - .gitkeep file inside the notebooks directory
    """
    # Define the project root and target directory
    project_root = Path("projects/PROJ-397-predicting-avian-foraging-behavior-from-")
    code_dir = project_root / "code"
    notebooks_dir = code_dir / "notebooks"
    
    # Create the directory structure
    notebooks_dir.mkdir(parents=True, exist_ok=True)
    
    # Create .gitkeep file to ensure directory is tracked by git
    gitkeep_path = notebooks_dir / ".gitkeep"
    gitkeep_path.touch()
    
    print(f"Successfully created directory: {notebooks_dir}")
    print(f"Created .gitkeep file: {gitkeep_path}")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
