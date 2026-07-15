import os
import sys
from pathlib import Path

def main():
    """
    Creates the required directory structure for the project:
    code/, data/raw, data/processed, results, and specs/.
    
    This script ensures that all necessary folders exist before 
    any data acquisition or processing tasks begin.
    """
    project_root = Path(__file__).resolve().parent.parent
    
    directories = [
        project_root / "code",
        project_root / "data" / "raw",
        project_root / "data" / "processed",
        project_root / "results",
        project_root / "specs"
    ]
    
    created_count = 0
    for dir_path in directories:
        if not dir_path.exists():
            dir_path.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {dir_path}")
            created_count += 1
        else:
            print(f"Directory already exists: {dir_path}")
    
    print(f"Setup complete. {created_count} new directories created.")
    return 0

if __name__ == "__main__":
    sys.exit(main())