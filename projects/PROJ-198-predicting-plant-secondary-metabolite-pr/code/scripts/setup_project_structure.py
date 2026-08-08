"""
Script to create the project directory structure for llmXive.
This implements T001: Create project structure per implementation plan.
"""
import os
from pathlib import Path
import sys

def main():
    # Define the project root (current directory where script is run from, or explicitly project root)
    # The task implies creating structure relative to the project root.
    # We assume the script is run from the project root.
    project_root = Path.cwd()
    
    # Define the required directories based on tasks.md and plan.md conventions
    # Note: tasks.md mentions `code/`, `data/raw`, `data/processed`, `tests/`
    # The existing API surface shows modules like `code/models/`, `code/data/`, `code/modeling/`, etc.
    
    directories = [
        "code",
        "code/models",
        "code/data",
        "code/data/raw",
        "code/data/processed",
        "code/data/interim",
        "code/modeling",
        "code/utils",
        "code/scripts",
        "code/tests",
        "code/tests/unit",
        "code/tests/integration",
        "data",
        "data/raw",
        "data/processed",
        "data/interim",
        "data/figures",
        "data/logs",
        "specs",
        "docs",
        "figures",
    ]

    created_count = 0
    skipped_count = 0

    print(f"Creating project structure in: {project_root}")

    for dir_path in directories:
        full_path = project_root / dir_path
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {dir_path}")
            created_count += 1
        else:
            # Check if it's a directory
            if full_path.is_dir():
                skipped_count += 1
            else:
                print(f"Warning: Path exists but is not a directory: {dir_path}")
    
    print(f"\nDone. Created {created_count} directories. Skipped {skipped_count} existing directories.")

    # Verify critical directories exist
    critical_dirs = ["code", "data/raw", "data/processed", "tests"]
    # Adjust for the actual structure used in this project (code/tests)
    critical_dirs = ["code", "data/raw", "data/processed", "code/tests"]
    
    missing = []
    for d in critical_dirs:
        if not (project_root / d).is_dir():
            missing.append(d)
    
    if missing:
        print(f"ERROR: Critical directories missing: {missing}")
        sys.exit(1)
    else:
        print("Verification: All critical directories exist.")

if __name__ == "__main__":
    main()