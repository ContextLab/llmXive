import os
from pathlib import Path
from typing import List

def create_structure() -> List[str]:
    """
    Creates the required project directory structure:
    - code/
    - tests/
    - data/raw/
    - data/processed/
    - code/models/
    - code/analysis/
    
    Returns a list of created directory paths.
    """
    root = Path.cwd()
    directories = [
        "code",
        "tests",
        "data/raw",
        "data/processed",
        "code/models",
        "code/analysis",
    ]
    
    created_paths = []
    for dir_name in directories:
        dir_path = root / dir_name
        if not dir_path.exists():
            dir_path.mkdir(parents=True, exist_ok=True)
            created_paths.append(str(dir_path))
        else:
            created_paths.append(str(dir_path))
            
    return created_paths

def main() -> None:
    """Entry point for script execution."""
    print("Creating project directory structure...")
    paths = create_structure()
    print("Directories created:")
    for p in paths:
        print(f"  - {p}")
    print("Done.")

if __name__ == "__main__":
    main()
