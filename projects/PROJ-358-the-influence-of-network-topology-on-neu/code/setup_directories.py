"""
Setup script to create the required directory structure for the project.
Implements T004: Setup directory structure for data/raw, data/processed, code/data, code/analysis, tests/
"""
import os
import sys
from pathlib import Path

def main():
    # Define the project root based on the task context
    # The project root is the parent of the 'code' directory
    current_file = Path(__file__).resolve()
    project_root = current_file.parent.parent

    # Define the relative paths to create
    # These paths must live under the project root as per constraints
    directories = [
        "data/raw",
        "data/processed",
        "code/data",
        "code/analysis",
        "tests/unit",
        "tests/integration",
        "docs",
        "contracts"
    ]

    created_count = 0
    skipped_count = 0

    print(f"Project Root: {project_root}")
    print("Creating directory structure...")

    for dir_path in directories:
        full_path = project_root / dir_path
        
        if full_path.exists():
            print(f"  [SKIP] {dir_path} (already exists)")
            skipped_count += 1
        else:
            full_path.mkdir(parents=True, exist_ok=True)
            print(f"  [CREATE] {dir_path}")
            created_count += 1

    print(f"\nSummary: {created_count} directories created, {skipped_count} already existed.")
    
    # Verify creation
    missing = []
    for dir_path in directories:
        if not (project_root / dir_path).exists():
            missing.append(dir_path)
    
    if missing:
        print(f"ERROR: The following directories were not created: {missing}")
        sys.exit(1)
    else:
        print("SUCCESS: All required directories are present.")
        sys.exit(0)

if __name__ == "__main__":
    main()
