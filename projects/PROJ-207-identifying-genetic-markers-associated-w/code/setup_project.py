import os
import sys
from pathlib import Path

def main():
    """
    Create the project directory structure as defined in T001.
    Directories created:
    - code/
    - data/raw/
    - data/processed/
    - data/interim/
    - state/
    - docs/
    - tests/
    """
    project_root = Path(__file__).resolve().parent.parent
    
    directories = [
        "code",
        "data/raw",
        "data/processed",
        "data/interim",
        "state",
        "docs",
        "tests"
    ]
    
    created_count = 0
    for dir_name in directories:
        dir_path = project_root / dir_name
        if not dir_path.exists():
            dir_path.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {dir_path.relative_to(project_root)}")
            created_count += 1
        else:
            print(f"Directory exists: {dir_path.relative_to(project_root)}")
    
    print(f"Project structure setup complete. {created_count} new directories created.")
    return 0

if __name__ == "__main__":
    sys.exit(main())