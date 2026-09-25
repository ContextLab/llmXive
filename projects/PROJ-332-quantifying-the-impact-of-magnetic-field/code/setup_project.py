import os
from pathlib import Path

def create_directories():
    """
    Create the project directory structure as defined in plan.md.
    
    Creates:
    - code/
    - data/raw/
    - data/intermediate/
    - data/processed/
    - outputs/
    - tests/
    - contracts/
    - .github/workflows/
    """
    base_dir = Path(__file__).resolve().parent.parent
    
    directories = [
        "code",
        "data/raw",
        "data/intermediate",
        "data/processed",
        "outputs",
        "tests",
        "contracts",
        ".github/workflows"
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
    
    print(f"Directory setup complete. Created {created_count} new directories.")
    return created_count

def main():
    """Entry point for directory creation script."""
    create_directories()

if __name__ == "__main__":
    main()
