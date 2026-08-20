import os
import sys
from pathlib import Path
from config import ensure_directories

def create_directories():
    """
    Create the required directory structure for the project.
    Directories created:
        - code/
        - tests/
        - data/raw/
        - data/processed/
        - state/
    """
    root = Path(__file__).resolve().parents[1]
    
    directories = [
        "code",
        "tests",
        "data/raw",
        "data/processed",
        "state"
    ]
    
    created = []
    for d in directories:
        dir_path = root / d
        if not dir_path.exists():
            dir_path.mkdir(parents=True, exist_ok=True)
            created.append(str(dir_path))
            print(f"Created directory: {dir_path}")
        else:
            print(f"Directory already exists: {dir_path}")
    
    # Ensure config paths are also valid (though config.py might handle this)
    ensure_directories()
    
    return created

def main():
    """Entry point for directory creation script."""
    print("Initializing project directory structure...")
    created = create_directories()
    if created:
        print(f"Successfully created {len(created)} directories.")
    else:
        print("All directories already exist.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
