"""
Project Setup Script for PROJ-503-predicting-plant-defense-compound-produc.

This script initializes the required directory structure for the project
as specified in task T001.
"""
import os
from pathlib import Path
import sys

# Define the project root based on the task requirements
# The task specifies paths relative to the project root, but we need to ensure
# they are created under the correct directory.
# Based on the task description, the root is:
# projects/PROJ-503-predicting-plant-defense-compound-produc/

# We will run this from the repo root or allow the user to specify the base.
# For robustness, we assume the script is run from the repository root
# and the project folder exists or is created relative to it.

def setup_project_structure():
    """Create all required directories for the project."""
    
    # Base project path as defined in the task
    base_path = Path("projects/PROJ-503-predicting-plant-defense-compound-produc")
    
    # List of required directories
    required_dirs = [
        "code",
        "data/raw",
        "data/processed",
        "data/paired",
        "logs",
        "outputs/models",
        "docs",
        "tests/contract",
        "tests/integration",
        "tests/unit"
    ]
    
    created_count = 0
    skipped_count = 0
    
    print(f"Setting up project structure in: {base_path.resolve()}")
    
    for dir_path in required_dirs:
        full_path = base_path / dir_path
        
        if full_path.exists():
            print(f"  [SKIP] {full_path} already exists.")
            skipped_count += 1
        else:
            full_path.mkdir(parents=True, exist_ok=True)
            print(f"  [CREATE] {full_path}")
            created_count += 1
    
    print(f"\nSetup complete.")
    print(f"  Created: {created_count} directories")
    print(f"  Skipped: {skipped_count} directories (already existed)")
    
    # Verify the structure
    print("\nVerifying directory structure...")
    missing = []
    for dir_path in required_dirs:
        full_path = base_path / dir_path
        if not full_path.exists():
            missing.append(str(full_path))
    
    if missing:
        print("ERROR: The following directories were not created:")
        for m in missing:
            print(f"  - {m}")
        sys.exit(1)
    else:
        print("All required directories verified successfully.")
        return True

def main():
    """Entry point for the script."""
    try:
        success = setup_project_structure()
        if success:
            print("\nProject setup successful.")
            sys.exit(0)
        else:
            print("\nProject setup failed.")
            sys.exit(1)
    except Exception as e:
        print(f"\nError during setup: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()