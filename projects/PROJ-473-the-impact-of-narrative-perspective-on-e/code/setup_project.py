import os
import sys
from pathlib import Path

def main():
    """
    Creates the required project directory structure for PROJ-473.
    Directories created: code/, data/, tests/, artifacts/
    Subdirectories for data and processing are also created.
    """
    project_root = Path(__file__).resolve().parent.parent
    
    # Define required directories relative to project root
    directories = [
        "code",
        "data/raw",
        "data/processed",
        "data/figures",
        "tests",
        "tests/integration",
        "artifacts",
        "specs"
    ]
    
    created_count = 0
    for dir_name in directories:
        dir_path = project_root / dir_name
        if not dir_path.exists():
            dir_path.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {dir_path}")
            created_count += 1
        else:
            print(f"Directory exists: {dir_path}")
    
    print(f"\nProject structure setup complete. {created_count} new directories created.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
