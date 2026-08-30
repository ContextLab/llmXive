import os
import sys
from pathlib import Path

def main():
    """
    Create the project directory structure as defined in plan.md.
    Directories created:
    - code/
    - data/raw/
    - data/processed/
    - tests/
    - artifacts/reports/
    - artifacts/figures/
    - state/
    """
    # Define the base directory (project root)
    base_dir = Path(__file__).resolve().parent.parent
    
    # Define the required directories relative to the project root
    required_dirs = [
        "code",
        "data/raw",
        "data/processed",
        "tests",
        "artifacts/reports",
        "artifacts/figures",
        "state"
    ]
    
    created_count = 0
    existing_count = 0
    
    for dir_path in required_dirs:
        full_path = base_dir / dir_path
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {full_path}")
            created_count += 1
        else:
            print(f"Directory already exists: {full_path}")
            existing_count += 1
    
    print(f"\nProject structure setup complete.")
    print(f"Created: {created_count} new directories.")
    print(f"Existing: {existing_count} directories.")

if __name__ == "__main__":
    main()