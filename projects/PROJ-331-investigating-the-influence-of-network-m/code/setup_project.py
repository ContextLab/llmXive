import os
import sys
from pathlib import Path

def create_directories():
    """
    Create the project directory structure as defined in T001.
    Directories created:
    - code/
    - tests/
    - data/raw/
    - data/processed/
    - data/logs/
    - results/
    - state/
    
    Returns:
        list: List of created directory paths
    """
    base_dir = Path(".")
    
    # Define the required directories relative to the project root
    directories = [
        "code",
        "tests",
        "data/raw",
        "data/processed",
        "data/logs",
        "results",
        "state"
    ]
    
    created_paths = []
    
    for dir_path in directories:
        full_path = base_dir / dir_path
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            created_paths.append(str(full_path))
            print(f"Created directory: {full_path}")
        else:
            # Ensure it is actually a directory
            if not full_path.is_dir():
                raise NotADirectoryError(f"Path exists but is not a directory: {full_path}")
            print(f"Directory already exists: {full_path}")
    
    return created_paths

def main():
    """
    Main entry point for the project setup script.
    Creates the required directory structure and exits.
    """
    print("Starting project directory creation...")
    try:
        created = create_directories()
        print(f"Successfully created {len(created)} directories.")
        print("Project structure ready.")
        return 0
    except Exception as e:
        print(f"Error creating directories: {e}", file=sys.stderr)
        return 1

if __name__ == "__main__":
    sys.exit(main())