import os
from pathlib import Path

def create_directory_structure():
    """
    Creates the required directory structure for the project.
    Implements task T004a.
    """
    root = Path(".")
    
    directories = [
        "data/raw",
        "data/processed",
        "results",
        "state",
        "contracts",
        "logs",
        "docs",
        "src/data",
        "src/graphs",
        "src/metrics",
        "src/analysis",
        "src/utils",
        "tests/unit",
        "tests/integration",
        "tests/contract"
    ]
    
    created_count = 0
    for dir_path in directories:
        full_path = root / dir_path
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            created_count += 1
            print(f"Created directory: {full_path}")
        else:
            print(f"Directory already exists: {full_path}")
    
    print(f"Directory structure setup complete. {created_count} new directories created.")
    return True

if __name__ == "__main__":
    create_directory_structure()