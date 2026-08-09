"""
Project Structure Initialization Script.

Creates the required directory structure for the llmXive science pipeline:
- code/: Source code modules
- data/: Raw and processed data
- tests/: Unit and integration tests
- artifacts/: Generated figures and reports
"""
import os
import sys
from pathlib import Path

def main():
    """Create the project directory structure."""
    # Define the base directory (project root)
    base_dir = Path(__file__).resolve().parent.parent
    
    # Define required directories relative to the project root
    required_dirs = [
        "code",
        "data",
        "data/raw",
        "data/processed",
        "tests",
        "tests/integration",
        "artifacts",
        "figures"
    ]
    
    created_count = 0
    existing_count = 0
    
    print(f"Initializing project structure at: {base_dir}")
    
    for dir_path in required_dirs:
        full_path = base_dir / dir_path
        
        if full_path.exists():
            print(f"  [SKIP] {dir_path} already exists")
            existing_count += 1
        else:
            full_path.mkdir(parents=True, exist_ok=True)
            print(f"  [CREATE] {dir_path}")
            created_count += 1
    
    print(f"\nInitialization complete: {created_count} directories created, {existing_count} already existed.")
    
    # Verify all directories exist
    all_exist = all((base_dir / d).exists() for d in required_dirs)
    
    if all_exist:
        print("SUCCESS: All required directories are present.")
        return 0
    else:
        print("FAILURE: Some directories could not be created.")
        return 1

if __name__ == "__main__":
    sys.exit(main())