import os
import sys
from pathlib import Path

def main():
    """
    Create the standard project directory structure for PROJ-761.
    
    Creates the following directories relative to the project root:
    - data/raw
    - data/processed
    - code
    - tests
    - artifacts/logs
    - artifacts/plots
    - artifacts/reports
    - contracts
    """
    # Define the base directory (project root)
    base_dir = Path.cwd()
    
    # Define relative paths to be created
    dirs_to_create = [
        "data/raw",
        "data/processed",
        "code",
        "tests",
        "artifacts/logs",
        "artifacts/plots",
        "artifacts/reports",
        "contracts"
    ]
    
    created_count = 0
    for dir_path in dirs_to_create:
        full_path = base_dir / dir_path
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {full_path}")
            created_count += 1
        else:
            print(f"Directory already exists: {full_path}")
    
    print(f"Project structure setup complete. {created_count} new directories created.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
