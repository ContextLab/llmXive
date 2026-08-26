"""
Task T001b: Verify Project Directory Structure
Dependency: T001a

This script asserts that the core directory structure required for the
project exists. It checks for `data/raw/`, `code/`, and `tests/`.

Exit Code:
  0 - All directories exist.
  1 - One or more directories are missing.
"""
import os
import sys
from pathlib import Path

def main():
    # Define the project root relative to where this script is run.
    # Assuming the script is run from the project root:
    # projects/PROJ-274-evaluating-the-impact-of-llm-generated-c/
    project_root = Path.cwd()
    
    required_dirs = [
        "data/raw",
        "code",
        "tests"
    ]
    
    missing_dirs = []
    
    print(f"Verifying structure in: {project_root}")
    
    for dir_name in required_dirs:
        full_path = project_root / dir_name
        if full_path.is_dir():
            print(f"[OK] Found: {full_path}")
        else:
            missing_dirs.append(full_path)
            print(f"[MISSING] {full_path}")
    
    if missing_dirs:
        print(f"\nError: {len(missing_dirs)} required directory(ies) missing.")
        for d in missing_dirs:
            print(f"  - {d}")
        sys.exit(1)
    
    print("\nAll required directories present.")
    sys.exit(0)

if __name__ == "__main__":
    main()