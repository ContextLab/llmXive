"""
Setup script to create the project directory structure.
This script ensures the required directories exist for the project.
"""
import os
from pathlib import Path

def main():
    # Project root relative to where the script is run
    # The task specifies: projects/PROJ-678-comparative-analysis-of-molecular-fingerprints/
    # But we are running from inside that project root (based on execution context)
    # The task description says: "Execute: mkdir -p data/raw data/processed code tests"
    # We assume the current working directory is the project root.
    
    project_root = Path(".")
    
    # Directories to create
    dirs = [
        "data/raw",
        "data/processed",
        "code",
        "tests"
    ]
    
    created_count = 0
    for dir_path in dirs:
        full_path = project_root / dir_path
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {full_path}")
            created_count += 1
        else:
            print(f"Directory already exists: {full_path}")
    
    # Create .gitkeep files in data directories to ensure they are tracked
    data_dirs = ["data/raw", "data/processed"]
    for dir_path in data_dirs:
        full_path = project_root / dir_path / ".gitkeep"
        if not full_path.exists():
            full_path.touch()
            print(f"Created .gitkeep in: {full_path.parent}")
    
    print(f"Setup complete. Created {created_count} new directories.")

if __name__ == "__main__":
    main()
