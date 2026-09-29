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
    - templates/
    - docs/
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
        "state",
        "templates",
        "docs"
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
    
    print(f"\nDirectory setup complete. Created {created_count} new directories.")
    return created_count

def main():
    """Entry point for the script."""
    setup_directories()

if __name__ == "__main__":
    main()
