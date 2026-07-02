import os
import sys
from pathlib import Path

def create_directories():
    """
    Creates the project directory structure as defined in plan.md.
    This function ensures all required folders for code, data, and tests exist.
    """
    base_dir = Path.cwd()
    
    # Define directory structure relative to the project root
    directories = [
        # Code modules
        "code/simulation",
        "code/gap_filling",
        "code/analysis",
        "code/pipeline",
        
        # Data storage
        "data/raw",
        "data/derived",
        "data/metadata",
        "data/results",
        
        # Test suites
        "tests/contract",
        "tests/unit",
        "tests/integration",
    ]
    
    created_count = 0
    existing_count = 0
    
    for dir_path in directories:
        full_path = base_dir / dir_path
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            created_count += 1
            print(f"Created: {full_path}")
        else:
            existing_count += 1
            print(f"Exists:  {full_path}")
    
    print(f"\nProject structure setup complete.")
    print(f"Directories created: {created_count}")
    print(f"Directories already existing: {existing_count}")
    return True

if __name__ == "__main__":
    create_directories()
