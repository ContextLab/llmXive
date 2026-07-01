"""
Project structure creation utility for PROJ-056.
Creates the directory tree defined in the implementation plan.
"""
import os
import sys
from pathlib import Path

def create_project_structure(base_dir: str = "projects/PROJ-056-the-impact-of-musical-training-on-functi") -> None:
    """
    Creates the required directory structure for the project.
    
    Args:
        base_dir: The root directory for the project structure.
    """
    # Define the directory tree based on the task requirements
    directories = [
        "code/data",
        "code/analysis",
        "code/utils",
        "tests/unit",
        "tests/integration",
        "tests/contract",
        "data/raw",
        "data/processed",
        "specs/001-the-impact-of-musical-training-on-functi",
        "contracts"
    ]
    
    base_path = Path(base_dir)
    
    # Create the base directory if it doesn't exist
    base_path.mkdir(parents=True, exist_ok=True)
    
    # Create each subdirectory
    for dir_path in directories:
        full_path = base_path / dir_path
        full_path.mkdir(parents=True, exist_ok=True)
        print(f"Created: {full_path}")
    
    # Create __init__.py files in Python package directories
    python_dirs = [
        "code",
        "code/data",
        "code/analysis",
        "code/utils",
        "tests",
        "tests/unit",
        "tests/integration",
        "tests/contract"
    ]
    
    for dir_path in python_dirs:
        full_path = base_path / dir_path / "__init__.py"
        if not full_path.exists():
            full_path.touch()
            print(f"Created: {full_path}")
    
    print(f"\nProject structure created successfully at: {base_path}")

if __name__ == "__main__":
    create_project_structure()