"""
Project structure creation utility for PROJ-558-consciousness-bootstrapping-self-aware-a.

This module provides functionality to create the required directory structure
for the consciousness bootstrapping research project.
"""
import os
from pathlib import Path


def create_structure():
    """
    Create the directory structure for the project.
    
    Creates the following structure under projects/PROJ-558-consciousness-bootstrapping-self-aware-a/:
    - data/raw
    - data/processed
    - code
    - tests
    - artifacts
    - artifacts/checkpoints
    - artifacts/results
    
    Returns:
        Path: The root project directory path
    """
    # Define the project root
    project_root = Path("projects/PROJ-558-consciousness-bootstrapping-self-aware-a")
    
    # Define all required directories
    directories = [
        project_root,
        project_root / "data" / "raw",
        project_root / "data" / "processed",
        project_root / "code",
        project_root / "tests",
        project_root / "artifacts",
        project_root / "artifacts" / "checkpoints",
        project_root / "artifacts" / "results",
    ]
    
    # Create all directories (parents=True ensures intermediate dirs are created)
    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)
        print(f"Created directory: {directory}")
    
    print(f"\nProject structure created successfully at: {project_root}")
    return project_root


if __name__ == "__main__":
    create_structure()