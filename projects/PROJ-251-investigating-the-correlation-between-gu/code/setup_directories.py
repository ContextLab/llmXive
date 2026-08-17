import os
import sys
from pathlib import Path

def create_directories():
    """
    Create the required project directory structure explicitly.
    
    Creates:
    - code/
    - data/raw
    - data/processed
    - data/results
    - specs/001-investigating-the-correlation-between-gu/contracts/
    
    Returns:
        list: List of created directory paths as strings
    """
    base_path = Path(__file__).resolve().parent.parent
    
    directories = [
        base_path / "code",
        base_path / "data" / "raw",
        base_path / "data" / "processed",
        base_path / "data" / "results",
        base_path / "specs" / "001-investigating-the-correlation-between-gu" / "contracts"
    ]
    
    created_paths = []
    for dir_path in directories:
        dir_path.mkdir(parents=True, exist_ok=True)
        created_paths.append(str(dir_path))
        print(f"Created directory: {dir_path}")
    
    return created_paths

def main():
    """Main entry point for directory creation."""
    print("Starting directory creation for PROJ-251...")
    created = create_directories()
    print(f"Successfully created {len(created)} directories.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
