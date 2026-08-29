import os
from pathlib import Path

def setup_directories():
    """
    Create the required directory structure for the project.
    
    Creates:
    - code/
    - data/
    - data/raw/
    - data/processed/
    - data/analysis/
    - tests/
    - contracts/
    - state/
    """
    base_dir = Path.cwd()
    
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
    
    created = []
    for dir_path in directories:
        full_path = base_dir / dir_path
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            created.append(str(full_path))
            print(f"Created directory: {full_path}")
        else:
            print(f"Directory already exists: {full_path}")
    
    return created

if __name__ == "__main__":
    setup_directories()
