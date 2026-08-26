"""
Script to initialize the project directory structure for llmXive project PROJ-084.

This script creates the required directories:
- code/
- data/raw/
- data/processed/
- data/results/
- tests/

It also creates .gitkeep files in data directories to ensure they are tracked by git.
"""
import os
from pathlib import Path


def main():
    """Create the project directory structure."""
    # Define the project root (current directory)
    root = Path(".")
    
    # Define directories to create
    directories = [
        "code",
        "data/raw",
        "data/processed",
        "data/results",
        "tests",
    ]
    
    created_dirs = []
    for dir_path in directories:
        full_path = root / dir_path
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            created_dirs.append(dir_path)
            print(f"Created directory: {full_path}")
        else:
            print(f"Directory already exists: {full_path}")
    
    # Create .gitkeep files in data directories to ensure they are tracked by git
    data_dirs = ["data/raw", "data/processed", "data/results"]
    for data_dir in data_dirs:
        gitkeep_path = root / data_dir / ".gitkeep"
        if not gitkeep_path.exists():
            gitkeep_path.touch()
            print(f"Created .gitkeep in: {gitkeep_path}")
        else:
            print(f".gitkeep already exists in: {gitkeep_path}")
    
    # Print summary
    print("\nDirectory structure initialization complete.")
    print("Created directories:", ", ".join(created_dirs) if created_dirs else "None (all existed)")


if __name__ == "__main__":
    main()
