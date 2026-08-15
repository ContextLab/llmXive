import os
import sys
from pathlib import Path

def main():
    """
    Initialize the notebooks directory for the project.
    
    Creates the directory structure:
    projects/PROJ-397-predicting-avian-foraging-behavior-from-/code/notebooks/
    
    And creates a .gitkeep file inside to ensure the directory is tracked by git.
    """
    project_root = Path(__file__).resolve().parent.parent
    notebooks_dir = project_root / "notebooks"
    
    # Create directory if it doesn't exist
    notebooks_dir.mkdir(parents=True, exist_ok=True)
    
    # Create .gitkeep file
    gitkeep_file = notebooks_dir / ".gitkeep"
    gitkeep_file.touch()
    
    print(f"Created directory: {notebooks_dir}")
    print(f"Created placeholder file: {gitkeep_file}")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
