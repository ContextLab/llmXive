import os
import sys
from pathlib import Path

def create_directories():
    """
    Creates the required project directory structure for the molecular permeability
    prediction pipeline.
    
    Creates:
    - data/raw/
    - data/processed/
    - code/models/
    - code/analysis/
    - code/utils/
    - code/config/
    - tests/contract/
    - tests/unit/
    - tests/integration/
    """
    project_root = Path(__file__).resolve().parent.parent
    
    directories = [
        "data/raw",
        "data/processed",
        "code/models",
        "code/analysis",
        "code/utils",
        "code/config",
        "tests/contract",
        "tests/unit",
        "tests/integration"
    ]
    
    created_count = 0
    existing_count = 0
    
    for dir_path in directories:
        full_path = project_root / dir_path
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {full_path}")
            created_count += 1
        else:
            existing_count += 1
    
    print(f"\nDirectory setup complete.")
    print(f"  Created: {created_count}")
    print(f"  Existing: {existing_count}")
    print(f"  Total: {len(directories)}")
    
    return created_count, existing_count

def main():
    """Entry point for directory creation script."""
    print("Initializing project directory structure...")
    created, existing = create_directories()
    print("Done.")

if __name__ == "__main__":
    main()
