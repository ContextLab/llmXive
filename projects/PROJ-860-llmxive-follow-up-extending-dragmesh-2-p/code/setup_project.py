import os
import sys
from pathlib import Path

def main():
    """
    Create the project directory structure for llmXive Follow-up.
    
    Executes the equivalent of:
    mkdir -p code tests data/raw data/generated data/results state/projects
    
    This script ensures the physical repository layout exists as per the plan.
    """
    # Define the project root relative to where this script is run or explicitly
    # Since the task implies running from the project root or creating it,
    # we assume the current working directory is the project root.
    project_root = Path(".")
    
    # Define the required directories relative to the project root
    required_dirs = [
        "code",
        "tests",
        "data/raw",
        "data/generated",
        "data/results",
        "state/projects"
    ]
    
    created_count = 0
    skipped_count = 0
    
    print(f"Creating project directory structure in: {project_root.absolute()}")
    
    for dir_path in required_dirs:
        full_path = project_root / dir_path
        try:
            if full_path.exists():
                print(f"  [SKIP] {dir_path} (already exists)")
                skipped_count += 1
            else:
                full_path.mkdir(parents=True, exist_ok=True)
                print(f"  [CREATE] {dir_path}")
                created_count += 1
        except OSError as e:
            print(f"  [ERROR] Failed to create {dir_path}: {e}")
            sys.exit(1)
    
    print(f"\nDirectory creation complete. Created: {created_count}, Skipped: {skipped_count}")
    
    # Verification step: list what was created to satisfy the "evidence" requirement
    print("\nVerification: Listing created directories...")
    for dir_path in required_dirs:
        full_path = project_root / dir_path
        if full_path.exists() and full_path.is_dir():
            print(f"  [OK] {dir_path}")
        else:
            print(f"  [FAIL] {dir_path} (missing)")
            sys.exit(1)

if __name__ == "__main__":
    main()
