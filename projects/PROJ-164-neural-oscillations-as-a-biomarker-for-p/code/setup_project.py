"""
Project Structure Initialization Script for llmXive PROJ-164.

This script implements Task T001a by creating the required directory tree
as specified in FR-001.
"""
import os
import sys
from pathlib import Path

def main():
    """
    Creates the project directory structure.
    
    Directories to create:
    - code/
    - code/utils/
    - tests/
    - data/raw
    - data/processed
    - data/synthetic
    - models/
    - docs/
    - docs/contracts/
    - state/projects/
    """
    project_root = Path.cwd()
    
    # Define the required directories relative to the project root
    required_dirs = [
        "code",
        "code/utils",
        "tests",
        "data/raw",
        "data/processed",
        "data/synthetic",
        "models",
        "docs",
        "docs/contracts",
        "state/projects",
    ]
    
    created_count = 0
    skipped_count = 0
    
    print(f"Initializing project structure at: {project_root}")
    
    for dir_path in required_dirs:
        full_path = project_root / dir_path
        try:
            if not full_path.exists():
                full_path.mkdir(parents=True, exist_ok=True)
                print(f"Created directory: {dir_path}")
                created_count += 1
            else:
                # Verify it is actually a directory
                if full_path.is_dir():
                    print(f"Directory exists (skipped): {dir_path}")
                    skipped_count += 1
                else:
                    print(f"ERROR: Path exists but is not a directory: {dir_path}")
                    sys.exit(1)
        except PermissionError:
            print(f"ERROR: Permission denied creating directory: {dir_path}")
            sys.exit(1)
        except Exception as e:
            print(f"ERROR: Failed to create directory {dir_path}: {e}")
            sys.exit(1)
    
    print(f"\nProject structure initialization complete.")
    print(f"Directories created: {created_count}")
    print(f"Directories skipped (already exist): {skipped_count}")
    
    # Verification step: List the created structure to confirm
    print("\nVerifying directory structure:")
    for dir_path in required_dirs:
        full_path = project_root / dir_path
        if full_path.exists() and full_path.is_dir():
            print(f"  [OK] {dir_path}")
        else:
            print(f"  [FAIL] {dir_path}")
            sys.exit(1)
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
