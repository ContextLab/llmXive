import os
import sys
from pathlib import Path

def ensure_directories():
    """
    Creates the project directory structure as defined in the implementation plan.
    Directories created:
    - code/
    - data/raw/
    - data/processed/
    - results/figures/
    - results/logs/
    - results/stats/
    - tests/
    """
    base_dir = Path(__file__).parent.parent
    
    directories = [
        "code",
        "data/raw",
        "data/processed",
        "results/figures",
        "results/logs",
        "results/stats",
        "tests"
    ]
    
    created_count = 0
    for dir_name in directories:
        dir_path = base_dir / dir_name
        if not dir_path.exists():
            dir_path.mkdir(parents=True, exist_ok=True)
            created_count += 1
            print(f"Created directory: {dir_path}")
        else:
            print(f"Directory already exists: {dir_path}")
    
    print(f"Project structure setup complete. {created_count} new directories created.")
    return created_count

def main():
    ensure_directories()

if __name__ == "__main__":
    main()
