import os
from pathlib import Path
import sys

def ensure_directories():
    """
    Create the required directory structure for the project.
    Ensures the following directories exist relative to the project root:
    - code/
    - data/raw/
    - data/interim/
    - data/processed/
    - data/results/
    - tests/unit/
    - tests/integration/
    - tests/contract/
    
    Returns:
        list: A list of absolute paths to the created/existing directories.
    """
    base_path = Path.cwd()
    
    required_dirs = [
        "code",
        "data/raw",
        "data/interim",
        "data/processed",
        "data/results",
        "tests/unit",
        "tests/integration",
        "tests/contract",
    ]
    
    created_paths = []
    
    for dir_name in required_dirs:
        full_path = base_path / dir_name
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            created_paths.append(str(full_path))
        else:
            created_paths.append(str(full_path))
            
    return created_paths

def main():
    """
    Main entry point for directory setup.
    Prints the paths of all ensured directories.
    """
    paths = ensure_directories()
    print("Directory structure ensured:")
    for p in paths:
        print(f"  - {p}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
