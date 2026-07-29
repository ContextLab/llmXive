"""
Project Structure Creator for PROJ-558-consciousness-bootstrapping-self-aware-a.

This script creates the required directory hierarchy for the project,
ensuring all necessary subdirectories exist for data, code, tests, and artifacts.
"""
import os
from pathlib import Path


def create_structure():
    """
    Creates the full directory structure for the consciousness bootstrapping project.
    
    Creates:
    - projects/PROJ-558-consciousness-bootstrapping-self-aware-a/
      - data/raw
      - data/processed
      - code
      - tests
      - artifacts
      - artifacts/checkpoints
      - artifacts/results
    """
    # Define the project root relative to the current working directory
    project_root = Path("projects/PROJ-558-consciousness-bootstrapping-self-aware-a")
    
    # Define all required subdirectories
    subdirs = [
        "data/raw",
        "data/processed",
        "code",
        "tests",
        "artifacts/checkpoints",
        "artifacts/results",
        # Additional standard directories for completeness based on API surface
        "code/models",
        "code/training",
        "code/evaluation",
        "code/analysis",
        "code/utils",
        "code/validation",
        "specs",
        "idea",
    ]
    
    created_count = 0
    existing_count = 0
    
    for subdir in subdirs:
        full_path = project_root / subdir
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            created_count += 1
            print(f"Created: {full_path}")
        else:
            existing_count += 1
            print(f"Already exists: {full_path}")
    
    print(f"\nProject structure setup complete.")
    print(f"  Created: {created_count} directories")
    print(f"  Already existed: {existing_count} directories")
    print(f"  Project root: {project_root.resolve()}")
    
    return project_root


if __name__ == "__main__":
    create_structure()
