import os
import sys
from pathlib import Path

def create_structure():
    """
    Create the project directory structure as defined in plan.md and tasks.md.
    
    Required directories:
    - src/
    - data/raw/
    - data/processed/
    - results/
    - results/meta_analysis/
    - tests/
    - specs/001-chemo-biomarker-discovery/contracts/
    - state/
    """
    # Define the project root (current directory)
    project_root = Path.cwd()
    
    # List of directories to create
    directories = [
        "src",
        "data/raw",
        "data/processed",
        "results",
        "results/meta_analysis",
        "tests",
        "specs/001-chemo-biomarker-discovery/contracts",
        "state"
    ]
    
    created_count = 0
    skipped_count = 0
    
    for dir_path in directories:
        full_path = project_root / dir_path
        try:
            if not full_path.exists():
                full_path.mkdir(parents=True, exist_ok=True)
                print(f"Created directory: {full_path}")
                created_count += 1
            else:
                print(f"Directory already exists: {full_path}")
                skipped_count += 1
        except OSError as e:
            print(f"Error creating directory {full_path}: {e}", file=sys.stderr)
            return 1
    
    print(f"\nProject structure setup complete.")
    print(f"Created: {created_count} directories")
    print(f"Skipped (already existed): {skipped_count} directories")
    
    # Verify structure
    print("\nVerifying directory structure...")
    missing = []
    for dir_path in directories:
        full_path = project_root / dir_path
        if not full_path.exists():
            missing.append(dir_path)
    
    if missing:
        print(f"ERROR: Missing directories: {missing}", file=sys.stderr)
        return 1
    else:
        print("All required directories verified.")
        return 0

if __name__ == "__main__":
    sys.exit(create_structure())
