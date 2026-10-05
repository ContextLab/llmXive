import os
from pathlib import Path


def main():
    """
    Create the required project directory structure.
    This script ensures the existence of:
    - code/
    - data/raw/
    - data/processed/
    - data/results/
    - tests/
    """
    base_dir = Path(__file__).resolve().parent.parent
    
    directories = [
        "code",
        "data/raw",
        "data/processed",
        "data/results",
        "tests"
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
    
    print(f"Setup complete. Created {created_count} new directory/directories.")


if __name__ == "__main__":
    main()
