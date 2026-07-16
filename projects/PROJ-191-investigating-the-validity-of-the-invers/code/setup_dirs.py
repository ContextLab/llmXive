"""
Script to initialize the full project directory structure for PROJ-191.
Creates all required subdirectories atomically.
"""
import os
import sys
from pathlib import Path

def main():
    # Define the project root relative to the current working directory
    # The task specifies the tree should be at projects/PROJ-191-...
    project_root = Path("projects/PROJ-191-investigating-the-validity-of-the-invers")
    
    # Define the relative subdirectories required
    # Note: Some paths overlap (e.g., code/ and code/data/), but os.makedirs handles this safely.
    subdirs = [
        "code",
        "tests",
        "data",
        "docs",
        "code/data",
        "code/models",
        "code/inference",
        "code/robustness",
        "code/utils",
        "data/raw",
        "data/processed",
        "data/results",
        "tests/unit",
        "tests/contract",
        "tests/integration",
    ]

    created_count = 0
    existing_count = 0

    for subdir in subdirs:
        full_path = project_root / subdir
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            created_count += 1
            print(f"Created: {full_path}")
        else:
            existing_count += 1

    print(f"\nDirectory initialization complete.")
    print(f"Project Root: {project_root.absolute()}")
    print(f"Directories created: {created_count}")
    print(f"Directories already existing: {existing_count}")

    # Verify the structure exists
    if not project_root.exists():
        print("ERROR: Project root was not created.", file=sys.stderr)
        sys.exit(1)

    return 0

if __name__ == "__main__":
    sys.exit(main())
