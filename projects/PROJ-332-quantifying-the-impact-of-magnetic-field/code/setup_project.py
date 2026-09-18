import os
import sys
from pathlib import Path

def main():
    """
    Create the project directory structure as specified in plan.md.
    
    Required directories:
    - code/
    - data/raw/
    - data/processed/
    - artifacts/
    - tests/
    """
    base_dir = Path(".")
    
    directories = [
        "code",
        "data/raw",
        "data/processed",
        "artifacts",
        "tests"
    ]
    
    created_count = 0
    for dir_path in directories:
        full_path = base_dir / dir_path
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {full_path}")
            created_count += 1
        else:
            print(f"Directory already exists: {full_path}")
    
    print(f"\nProject structure setup complete. Created {created_count} new directories.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
