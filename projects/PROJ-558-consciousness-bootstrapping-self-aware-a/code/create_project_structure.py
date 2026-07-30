"""
Script to create the project directory structure for PROJ-558.
"""
import os
from pathlib import Path

def create_structure():
    """Create the required directory structure."""
    base_dir = Path("projects/PROJ-558-consciousness-bootstrapping-self-aware-a")
    
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
        dir_path = base_dir / subdir
        dir_path.mkdir(parents=True, exist_ok=True)
        created_dirs.append(str(dir_path))
        print(f"Created directory: {dir_path}")
    
    print(f"\nProject structure created at: {base_dir}")
    print(f"Total directories created: {len(created_dirs)}")
    return created_dirs

if __name__ == "__main__":
    create_structure()
