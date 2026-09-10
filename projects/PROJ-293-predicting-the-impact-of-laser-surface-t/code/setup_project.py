import os
from pathlib import Path

def main():
    """
    Create the project directory structure as defined in T001.
    Directories created:
    - code/
    - data/
    - tests/
    - state/
    - models/
    - data/raw/
    - data/processed/
    - reports/
    """
    base_dir = Path.cwd()
    
    directories = [
        "code",
        "data",
        "tests",
        "state",
        "models",
        "data/raw",
        "data/processed",
        "reports"
    ]
    
    created_count = 0
    existing_count = 0
    
    for dir_path in directories:
        full_path = base_dir / dir_path
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {full_path}")
            created_count += 1
        else:
            print(f"Directory already exists: {full_path}")
            existing_count += 1
    
    print(f"\nProject structure setup complete.")
    print(f"Directories created: {created_count}")
    print(f"Directories already existing: {existing_count}")
    
    # Verify all directories exist
    all_exist = all((base_dir / d).exists() and (base_dir / d).is_dir() for d in directories)
    if not all_exist:
        missing = [d for d in directories if not (base_dir / d).exists()]
        raise FileNotFoundError(f"Failed to create directories: {missing}")
    
    return 0

if __name__ == "__main__":
    exit(main())