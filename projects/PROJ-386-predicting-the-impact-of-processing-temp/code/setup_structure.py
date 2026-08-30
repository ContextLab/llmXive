import os
import sys
from pathlib import Path

def main():
    """
    Creates the project directory structure as defined in plan.md.
    
    Required directories:
    - code/
    - data/raw/
    - data/processed/
    - data/artifacts/
    - tests/
    - state/
    """
    project_root = Path(__file__).resolve().parent.parent
    
    directories = [
        "code",
        "data/raw",
        "data/processed",
        "data/artifacts",
        "tests",
        "state"
    ]
    
    created_count = 0
    for dir_name in directories:
        dir_path = project_root / dir_name
        if not dir_path.exists():
            dir_path.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {dir_path}")
            created_count += 1
        else:
            print(f"Directory already exists: {dir_path}")
    
    print(f"Project structure setup complete. Created {created_count} new directories.")
    return 0

if __name__ == "__main__":
    sys.exit(main())