"""
Project structure initialization script.
Creates the required directory tree for the llmXive science pipeline.
"""
import os
from pathlib import Path


def create_directories():
    """
    Create the project directory structure as defined in T001a and T001b.
    
    Required paths:
    - code/
    - code/models/
    - code/utils/
    - code/simulations/
    - data/raw/
    - data/processed/
    - results/
    - tests/
    - state/
    
    Returns:
        list: List of created directory paths (as strings).
    """
    base_dir = Path(__file__).parent.parent
    
    directories = [
        "code",
        "code/models",
        "code/utils",
        "code/simulations",
        "data/raw",
        "data/processed",
        "results",
        "tests",
        "state",
    ]
    
    created = []
    for dir_path in directories:
        full_path = base_dir / dir_path
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            created.append(str(full_path))
            print(f"Created directory: {full_path}")
        else:
            print(f"Directory already exists: {full_path}")
    
    return created


def main():
    """Entry point for directory creation."""
    print("Initializing project directory structure...")
    created_dirs = create_directories()
    print(f"\nTotal directories created/verified: {len(created_dirs)}")
    return 0


if __name__ == "__main__":
    exit(main())
