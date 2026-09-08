"""
Directory creation for project artifacts.

Creates the necessary directory structure for storing models,
reports, figures, and processed data.
"""
import os
from pathlib import Path

def main():
    """
    Create all required artifact directories.
    
    Creates directories under the project root for:
    - data/raw, data/processed, data/split
    - artifacts/models, artifacts/reports, artifacts/figures
    """
    # Get project root
    project_root = Path(__file__).parent.parent
    
    # Define directory structure
    directories = [
        "data/raw",
        "data/processed",
        "data/split",
        "artifacts/models",
        "artifacts/reports",
        "artifacts/figures",
    ]
    
    # Create directories
    for dir_path in directories:
        full_path = project_root / dir_path
        full_path.mkdir(parents=True, exist_ok=True)
        print(f"Created directory: {full_path}")
    
    # Create .gitkeep files to ensure directories are tracked
    gitkeep_path = project_root / "data" / ".gitkeep"
    if not gitkeep_path.exists():
        gitkeep_path.touch()
        print(f"Created .gitkeep in data/")
        
    gitkeep_path = project_root / "artifacts" / ".gitkeep"
    if not gitkeep_path.exists():
        gitkeep_path.touch()
        print(f"Created .gitkeep in artifacts/")

if __name__ == "__main__":
    main()
