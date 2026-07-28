"""
Script to create the directory structure for project PROJ-558.
This satisfies task T001a.
"""
import os
from pathlib import Path

def create_structure():
    project_root = Path("projects/PROJ-558-consciousness-bootstrapping-self-aware-a")
    
    # Define the required subdirectories
    subdirs = [
        "data/raw",
        "data/processed",
        "code",
        "tests",
        "artifacts",
        "artifacts/checkpoints",
        "artifacts/results"
    ]
    
    created_dirs = []
    
    for subdir in subdirs:
        full_path = project_root / subdir
        full_path.mkdir(parents=True, exist_ok=True)
        created_dirs.append(str(full_path))
        print(f"Created: {full_path}")
    
    # Create a .gitkeep in each directory to ensure they are tracked by git
    # even if they are empty initially
    for subdir in subdirs:
        full_path = project_root / subdir / ".gitkeep"
        full_path.touch()
        print(f"Created: {full_path}")
    
    print(f"\nProject structure created successfully at {project_root}")
    return created_dirs

if __name__ == "__main__":
    create_structure()
