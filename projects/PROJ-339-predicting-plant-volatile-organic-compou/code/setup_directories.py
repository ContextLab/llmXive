import os
import sys
from pathlib import Path

def create_directories():
    """
    Create the standard project directory structure for the llmXive pipeline.
    This function ensures all necessary folders exist for data storage,
    code organization, and specifications.

    Directories created:
    - code/: Source code modules
    - tests/: Test suites
    - data/raw/: Raw downloaded/generated data
    - data/processed/: Processed/cleaned data
    - data/results/: Analysis results and reports
    - data/models/: Trained model artifacts
    - specs/: Feature specifications and contracts
    """
    base_dir = Path(".")
    
    directories = [
        "code",
        "tests",
        "data/raw",
        "data/processed",
        "data/results",
        "data/models",
        "specs"
    ]
    
    created_count = 0
    for dir_name in directories:
        dir_path = base_dir / dir_name
        if not dir_path.exists():
            dir_path.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {dir_path}")
            created_count += 1
        else:
            print(f"Directory already exists: {dir_path}")
    
    print(f"Directory setup complete. {created_count} new directories created.")
    return True

def main():
    """Entry point for script execution."""
    create_directories()

if __name__ == "__main__":
    main()
