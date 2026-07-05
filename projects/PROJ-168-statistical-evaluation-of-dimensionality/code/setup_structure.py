"""
Script to initialize the project directory structure for the gene regulation study.
Creates the necessary folders for raw data, processed data, results, code, and tests.
"""
import os
from pathlib import Path

def create_project_structure():
    """
    Creates the directory structure defined in the implementation plan.
    Path: projects/001-gene-regulation/{data/raw, data/processed, results, code, tests}
    """
    base_dir = Path("projects") / "001-gene-regulation"
    
    directories = [
        base_dir / "data" / "raw",
        base_dir / "data" / "processed",
        base_dir / "results",
        base_dir / "code",
        base_dir / "tests"
    ]

    created_count = 0
    for directory in directories:
        if not directory.exists():
            directory.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {directory}")
            created_count += 1
        else:
            print(f"Directory already exists: {directory}")
    
    print(f"Project structure initialization complete. {created_count} new directories created.")
    return created_count

if __name__ == "__main__":
    create_project_structure()