import os
import sys
from pathlib import Path

def create_directories():
    """
    Create the project directory structure as defined in the implementation plan.
    
    Directories created:
    - src/data, src/models, src/analysis
    - data/raw, data/processed, data/interim
    - tests/contract, tests/unit, tests/integration
    - docs
    """
    base_dir = Path(__file__).resolve().parent.parent
    
    directories = [
        "src/data",
        "src/models",
        "src/analysis",
        "data/raw",
        "data/processed",
        "data/interim",
        "tests/contract",
        "tests/unit",
        "tests/integration",
        "docs"
    ]
    
    created_count = 0
    for dir_name in directories:
        dir_path = base_dir / dir_name
        if not dir_path.exists():
            dir_path.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {dir_path}")
            created_count += 1
        else:
            print(f"Directory already exists: {dir_path}")
    
    print(f"\nProject structure setup complete. Created {created_count} new directories.")
    return True

if __name__ == "__main__":
    create_directories()
