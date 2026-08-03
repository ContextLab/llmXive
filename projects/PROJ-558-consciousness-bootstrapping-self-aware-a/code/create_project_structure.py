"""
Script to create the directory structure for the Consciousness Bootstrapping project.
This script creates the required hierarchy under the project root.
"""
import os
from pathlib import Path

def create_structure():
    """
    Creates the directory structure for project PROJ-558.
    
    Structure:
    projects/PROJ-558-consciousness-bootstrapping-self-aware-a/
    ├── data/
    │   ├── raw/
    │   └── processed/
    ├── code/
    ├── tests/
    ├── artifacts/
    │   ├── checkpoints/
    │   └── results/
    """
    # Define the project root relative to where this script is run
    # Assuming the script is run from the project root or code directory
    # We will create it relative to the current working directory
    base_path = Path.cwd()
    
    project_root = base_path / "projects" / "PROJ-558-consciousness-bootstrapping-self-aware-a"
    
    # Define subdirectories
    subdirs = [
        "data/raw",
        "data/processed",
        "code",
        "tests",
        "artifacts/checkpoints",
        "artifacts/results",
        "artifacts/figures", # Added for completeness based on common patterns, though not explicitly in T001a, often needed for plots
    ]
    
    created_count = 0
    
    for subdir in subdirs:
        dir_path = project_root / subdir
        if not dir_path.exists():
            dir_path.mkdir(parents=True, exist_ok=True)
            print(f"Created: {dir_path}")
            created_count += 1
        else:
            print(f"Exists: {dir_path}")
    
    print(f"\nProject structure created at: {project_root}")
    print(f"Total new directories created: {created_count}")
    
    # Verify structure
    print("\nVerifying structure...")
    for subdir in subdirs:
        dir_path = project_root / subdir
        if dir_path.exists():
            print(f"  [OK] {dir_path}")
        else:
            print(f"  [FAIL] {dir_path}")
    
    return project_root

if __name__ == "__main__":
    create_structure()
