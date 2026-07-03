"""
Project structure initialization script.
Creates the required directory hierarchy for the research pipeline.
"""
import os
from pathlib import Path

def create_project_structure():
    """
    Create the standard project directory structure at the repository root.
    
    Creates:
    - code/ (source code)
    - tests/ (unit and integration tests)
    - data/raw/ (raw downloaded datasets)
    - data/processed/ (cleaned/transformed data)
    - data/results/ (analysis outputs, figures, summaries)
    - state/ (project state tracking, checksums)
    """
    root = Path(".")
    
    directories = [
        "code",
        "tests",
        "data/raw",
        "data/processed",
        "data/results",
        "state"
    ]
    
    created_count = 0
    for dir_path in directories:
        full_path = root / dir_path
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {full_path}")
            created_count += 1
        else:
            print(f"Directory already exists: {full_path}")
    
    print(f"\nProject structure initialization complete. Created {created_count} new directories.")
    return created_count

if __name__ == "__main__":
    create_project_structure()