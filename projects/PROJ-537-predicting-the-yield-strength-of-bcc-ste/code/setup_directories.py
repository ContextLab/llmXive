"""
Setup script for PROJ-537: Predicting the Yield Strength of BCC Steels.
Creates the required project directory structure as specified in T001.
"""
import os
import sys
from pathlib import Path

def main():
    # Define the project root (current working directory)
    project_root = Path.cwd()
    
    # Define all required directories relative to the project root
    required_dirs = [
        "code",
        "data",
        "data/raw",
        "data/intermediate",
        "data/processed",
        "data/provenance",
        "data/results",
        "tests",
        "tests/unit",
        "tests/integration",
        "tests/contract",
    ]
    
    created_count = 0
    existing_count = 0
    
    print(f"Creating project directories for {project_root}...")
    
    for dir_path in required_dirs:
        full_path = project_root / dir_path
        
        if full_path.exists():
            # Check if it is a directory
            if full_path.is_dir():
                print(f"  [SKIP] {dir_path} (already exists)")
                existing_count += 1
            else:
                print(f"  [ERROR] {dir_path} exists but is not a directory")
                return 1
        else:
            # Create the directory and any necessary parents
            full_path.mkdir(parents=True, exist_ok=True)
            print(f"  [CREATE] {dir_path}")
            created_count += 1
    
    print(f"\nSetup complete.")
    print(f"  Created: {created_count} directories")
    print(f"  Skipped: {existing_count} directories")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())