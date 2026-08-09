import os
import sys
from pathlib import Path

def create_directories():
    """
    Create the project directory structure as defined in T004.
    
    Required directories:
    - code/
    - tests/
    - data/raw
    - data/processed
    - data/simulations
    - data/reports
    - docs/
    
    Returns:
        bool: True if all directories were created successfully, False otherwise.
    """
    project_root = Path(__file__).resolve().parent.parent
    
    directories = [
        "code",
        "tests",
        "data/raw",
        "data/processed",
        "data/simulations",
        "data/reports",
        "docs"
    ]
    
    created = []
    failed = []
    
    for dir_name in directories:
        dir_path = project_root / dir_name
        try:
            dir_path.mkdir(parents=True, exist_ok=True)
            created.append(str(dir_path))
            print(f"Created directory: {dir_path}")
        except Exception as e:
            failed.append((dir_name, str(e)))
            print(f"Failed to create directory {dir_name}: {e}", file=sys.stderr)
    
    if failed:
        print(f"\nSummary: {len(created)} directories created, {len(failed)} failed.", file=sys.stderr)
        return False
    
    print(f"\nSuccessfully created {len(created)} directories.")
    return True

if __name__ == "__main__":
    success = create_directories()
    sys.exit(0 if success else 1)
