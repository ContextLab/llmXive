import os
from pathlib import Path

def create_directories():
    """
    Creates the required directory structure for the project:
    - code/
    - tests/
    - state/
    
    This function ensures that the core structural directories exist
    as per plan.md requirements.
    """
    base_path = Path(__file__).resolve().parent.parent
    
    directories = [
        base_path / "code",
        base_path / "tests",
        base_path / "state"
    ]
    
    created_count = 0
    for directory in directories:
        if not directory.exists():
            directory.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {directory}")
            created_count += 1
        else:
            print(f"Directory already exists: {directory}")
    
    return created_count

def main():
    """Entry point for directory creation script."""
    print("Initializing project directories...")
    count = create_directories()
    print(f"Successfully created/verified {count} new directories.")
    print("Project structure initialization complete.")

if __name__ == "__main__":
    main()
