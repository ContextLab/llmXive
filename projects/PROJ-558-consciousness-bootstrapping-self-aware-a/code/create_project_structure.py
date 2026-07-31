"""
Project Structure Creator for llmXive Pipeline.

This script creates the required directory structure for the project:
projects/PROJ-558-consciousness-bootstrapping-self-aware-a/

Subdirectories:
- data/raw
- data/processed
- code
- tests
- artifacts
- artifacts/checkpoints
- artifacts/results
"""

import os
from pathlib import Path


def create_structure():
    """
    Create the full directory structure for the project.
    Prints the created paths to stdout for verification.
    """
    # Define the project root relative to the current working directory
    # The task specifies the path relative to the project root
    project_root = Path("projects/PROJ-558-consciousness-bootstrapping-self-aware-a")
    
    # Define all required subdirectories
    subdirs = [
        "data/raw",
        "data/processed",
        "code",
        "tests",
        "artifacts",
        "artifacts/checkpoints",
        "artifacts/results"
    ]
    
    created_paths = []
    
    for subdir in subdirs:
        full_path = project_root / subdir
        full_path.mkdir(parents=True, exist_ok=True)
        created_paths.append(str(full_path))
        print(f"Created: {full_path}")
    
    # Ensure the root project directory itself exists (mkdir with parents=True handles this)
    print(f"\nProject structure created at: {project_root}")
    return created_paths


if __name__ == "__main__":
    create_structure()
