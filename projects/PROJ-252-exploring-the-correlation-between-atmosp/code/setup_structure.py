import os
import sys
from pathlib import Path

def main():
    """
    Sets up the required directory structure for the project.
    Creates: data/raw, data/interim, data/processed, code, tests, docs
    """
    project_root = Path(__file__).resolve().parent.parent
    
    directories = [
        project_root / "data" / "raw",
        project_root / "data" / "interim",
        project_root / "data" / "processed",
        project_root / "code",
        project_root / "tests",
        project_root / "docs",
    ]
    
    created_count = 0
    for directory in directories:
        if not directory.exists():
            directory.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {directory}")
            created_count += 1
        else:
            print(f"Directory already exists: {directory}")
    
    print(f"Setup complete. Created {created_count} new directories.")
    return 0

if __name__ == "__main__":
    sys.exit(main())