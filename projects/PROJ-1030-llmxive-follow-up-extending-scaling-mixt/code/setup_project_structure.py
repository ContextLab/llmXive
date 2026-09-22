import os
import sys
from pathlib import Path

def create_directories():
    """
    Create the project directory structure as defined in T001.
    Directories are created relative to the project root.
    """
    # Define the directory structure relative to the project root
    # Assuming the script is run from the project root or code/
    # We will resolve paths relative to the current working directory
    # but ensure they align with the project tree requirements.
    
    # Base paths
    base_path = Path.cwd()
    
    # Define required directories based on T001 task description
    required_dirs = [
        "code",
        "code/utils",
        "data/raw",
        "data/processed",
        "tests/unit",
        "tests/integration",
        "docs/figures",
        "state"
    ]
    
    created_count = 0
    existing_count = 0
    
    for dir_path in required_dirs:
        full_path = base_path / dir_path
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            created_count += 1
            print(f"Created directory: {full_path}")
        else:
            existing_count += 1
            print(f"Directory already exists: {full_path}")
    
    print(f"\nProject structure setup complete.")
    print(f"Created: {created_count} directories")
    print(f"Existing: {existing_count} directories")
    
    return True

def main():
    """Entry point for the project structure setup."""
    try:
        create_directories()
        return 0
    except Exception as e:
        print(f"Error setting up project structure: {e}", file=sys.stderr)
        return 1

if __name__ == "__main__":
    sys.exit(main())
