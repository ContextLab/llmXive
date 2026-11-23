"""
Script to create the required directory structure for PROJ-558.
This script ensures all necessary folders for data, code, tests, and artifacts exist.
"""
import os
from pathlib import Path

def create_structure():
    base_dir = Path("projects/PROJ-558-consciousness-bootstrapping-self-aware-a")
    
    # Define the required subdirectories relative to the project root
    # Note: The task asks for structure under the project name, but the 
    # existing API surface implies the code lives in 'code/' at the root.
    # We will create the specific project folder as requested, and ensure 
    # the standard project root folders (code/, tests/, data/) exist as well
    # to support the existing imports.
    
    project_specific_dirs = [
        "data/raw",
        "data/processed",
        "artifacts/checkpoints",
        "artifacts/results",
    ]
    
    # Standard project root directories (required for existing imports)
    root_dirs = [
        "code",
        "code/models",
        "code/training",
        "code/evaluation",
        "code/analysis",
        "code/utils",
        "tests",
        "tests/unit",
        "tests/unit/models",
        "tests/unit/training",
        "tests/unit/evaluation",
        "tests/unit/analysis",
        "data",
        "data/raw",
        "data/processed",
        "artifacts",
        "artifacts/checkpoints",
        "artifacts/results",
        "docs",
    ]
    
    created_count = 0
    
    # Create project-specific structure
    for subdir in project_specific_dirs:
        path = base_dir / subdir
        if not path.exists():
            path.mkdir(parents=True, exist_ok=True)
            created_count += 1
            print(f"Created: {path}")
    
    # Create standard root structure
    for subdir in root_dirs:
        path = Path(subdir)
        if not path.exists():
            path.mkdir(parents=True, exist_ok=True)
            created_count += 1
            print(f"Created: {path}")
    
    print(f"\nTotal directories created: {created_count}")
    print(f"Project structure ready at: {base_dir}")

if __name__ == "__main__":
    create_structure()