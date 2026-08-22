import os
from pathlib import Path

def setup_directories():
    """
    Create the required directory structure for the project.
    
    Creates the following directories relative to the project root:
    - code/
    - data/
    - data/raw/
    - data/processed/
    - data/analysis/
    - tests/
    - contracts/
    - state/
    
    Returns:
        dict: A dictionary mapping directory names to their absolute paths.
    """
    base_path = Path(__file__).resolve().parent.parent
    
    directories = [
        "code",
        "data",
        "data/raw",
        "data/processed",
        "data/analysis",
        "tests",
        "contracts",
        "state"
    ]
    
    created_paths = {}
    
    for dir_name in directories:
        full_path = base_path / dir_name
        try:
            full_path.mkdir(parents=True, exist_ok=True)
            created_paths[dir_name] = str(full_path)
            print(f"Created directory: {full_path}")
        except OSError as e:
            print(f"Error creating directory {full_path}: {e}")
            raise
    
    return created_paths

if __name__ == "__main__":
    setup_directories()
