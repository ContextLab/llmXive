import os
import sys
from pathlib import Path

def create_structure():
    """
    Wrapper to create the project structure.
    This ensures the directory tree matches the implementation plan.
    """
    base_path = Path(__file__).parent
    
    directories = [
        "src/ingestion",
        "src/modeling",
        "src/visualization",
        "src/utils",
        "tests/contract",
        "tests/integration",
        "tests/unit",
        "data/raw",
        "data/processed",
        "docs"
    ]
    
    created_count = 0
    for dir_name in directories:
        full_path = base_path / dir_name
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            created_count += 1
        elif not full_path.is_dir():
            raise RuntimeError(f"Error: {full_path} exists but is not a directory.")
    
    return created_count

if __name__ == "__main__":
    count = create_structure()
    print(f"Project structure initialized. {count} directories created.")