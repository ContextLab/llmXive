"""
T001: Create project directory structure.

This script creates the necessary directory hierarchy for the 
Lorentz Violation testing project as specified in the tasks.md.

Directories created:
- code/data, code/analysis, code/utils
- data/raw, data/processed, data/simulations, data/results
- tests
"""
import os
import sys
from pathlib import Path

def create_directories():
    """Create the project directory structure."""
    # Define relative paths based on the task description
    # The task specifies paths relative to the project root
    directories = [
        "code/data",
        "code/analysis",
        "code/utils",
        "data/raw",
        "data/processed",
        "data/simulations",
        "data/results",
        "tests"
    ]

    root = Path(".")
    created = []
    skipped = []

    for dir_path in directories:
        full_path = root / dir_path
        try:
            full_path.mkdir(parents=True, exist_ok=True)
            created.append(str(full_path))
        except PermissionError:
            print(f"Permission denied creating: {full_path}", file=sys.stderr)
            skipped.append(str(full_path))
        except Exception as e:
            print(f"Error creating {full_path}: {e}", file=sys.stderr)
            skipped.append(str(full_path))

    if created:
        print(f"Created {len(created)} directories:")
        for d in created:
            print(f"  - {d}")
    
    if skipped:
        print(f"Skipped {len(skipped)} directories due to errors:")
        for d in skipped:
            print(f"  - {d}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(create_directories())
