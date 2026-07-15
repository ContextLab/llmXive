"""
T001: Create project structure per implementation plan.

This script initializes the directory structure required for the
llmXive research pipeline, creating the necessary folders for source code,
data artifacts, tests, and state tracking.

Directories created:
  - code/ (source code)
  - data/raw/ (raw input data)
  - data/processed/ (processed data)
  - data/artifacts/ (intermediate/final artifacts)
  - tests/unit/ (unit tests)
  - tests/integration/ (integration tests)
  - state/ (state hashes and logs)
  - specs/ (feature specifications)
  - contracts/ (schema contracts)
  - figures/ (plots and visualizations)

Note: This script creates empty __init__.py files in Python package directories
to ensure they are recognized as packages.
"""
import os
import sys
from pathlib import Path

def create_structure():
    """Create the project directory structure."""
    # Define relative paths based on project root
    base_dirs = [
        "code",
        "data/raw",
        "data/processed",
        "data/artifacts",
        "tests/unit",
        "tests/integration",
        "state",
        "specs",
        "contracts",
        "figures",
        "code/utils",
        "code/data",
        "code/models",
        "code/eval",
        "code/config",
        "code/cli",
    ]

    created_count = 0
    skipped_count = 0

    for dir_path in base_dirs:
        full_path = Path(dir_path)
        
        # Create parent directories if they don't exist
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {full_path}")
            created_count += 1
        else:
            print(f"Directory already exists: {full_path}")
            skipped_count += 1

        # Create __init__.py for Python package directories
        if "code" in dir_path or "tests" in dir_path:
            init_file = full_path / "__init__.py"
            if not init_file.exists():
                # Create an empty __init__.py to mark as package
                init_file.touch()
                print(f"Created: {init_file}")
                created_count += 1
            else:
                print(f"__init__.py already exists: {init_file}")
                skipped_count += 1

    print(f"\nProject structure creation complete.")
    print(f"Directories created: {created_count}")
    print(f"Directories skipped (already exist): {skipped_count}")
    
    # Verify critical paths exist
    critical_paths = [
        "code",
        "data/processed",
        "tests/unit",
        "state",
        "contracts",
    ]
    
    missing = []
    for path in critical_paths:
        if not Path(path).exists():
            missing.append(path)
    
    if missing:
        print(f"\nERROR: Critical paths missing: {missing}")
        sys.exit(1)
    
    print("\nAll critical paths verified.")

if __name__ == "__main__":
    create_structure()