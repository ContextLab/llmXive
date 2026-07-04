"""
T001: Create project structure per implementation plan.

This script initializes the directory structure required for the
Predicting Coral Bleaching Susceptibility project.

Directories created:
- code/
- data/raw
- data/processed
- data/models
- tests/
"""
import os
from pathlib import Path

def main():
    # Define the project root (current working directory)
    project_root = Path(".")
    
    # Define the required directory structure
    directories = [
        "code",
        "data/raw",
        "data/processed",
        "data/models",
        "tests",
    ]
    
    created_count = 0
    
    for dir_path in directories:
        full_path = project_root / dir_path
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {full_path}")
            created_count += 1
        else:
            print(f"Directory already exists: {full_path}")
    
    print(f"\nProject structure setup complete. {created_count} new directories created.")

if __name__ == "__main__":
    main()