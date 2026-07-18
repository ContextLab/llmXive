"""
Project Structure Initialization Script.

This script creates the required directory structure for the llmXive project
PROJ-548-exploring-the-relationship-between-prime.
"""
import os
import sys
from pathlib import Path

def main():
    """Create the project directory structure."""
    # Define the project root (assumed to be the current working directory or 'projects/PROJ-548...')
    # The task description implies paths relative to the project root.
    # We will assume the script is run from the project root.
    project_root = Path.cwd()

    # Define the required directories based on the task description
    # Paths are relative to project_root
    required_dirs = [
        "src/data",
        "src/analysis",
        "src/utils",
        "src/cli",
        "tests/unit",
        "tests/integration",
        "data/raw",
        "data/processed",
        "data/results",
        "results",
        "state"
    ]

    created_count = 0
    existing_count = 0

    print(f"Initializing project structure in: {project_root}")

    for dir_path in required_dirs:
        full_path = project_root / dir_path
        
        if full_path.exists():
            print(f"  [OK] Directory already exists: {dir_path}")
            existing_count += 1
        else:
            full_path.mkdir(parents=True, exist_ok=True)
            print(f"  [CREATED] {dir_path}")
            created_count += 1

    print(f"\nStructure initialization complete.")
    print(f"  New directories: {created_count}")
    print(f"  Existing directories: {existing_count}")
    print(f"  Total directories managed: {created_count + existing_count}")

    # Verify the structure
    missing = []
    for dir_path in required_dirs:
        if not (project_root / dir_path).exists():
            missing.append(dir_path)
    
    if missing:
        print(f"\n[ERROR] The following directories were NOT created: {missing}")
        return 1
    
    print("\n[SUCCESS] All required directories are present.")
    return 0

if __name__ == "__main__":
    sys.exit(main())