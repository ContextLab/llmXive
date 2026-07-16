"""
Project initialization script for PROJ-925-llmxive-follow-up-extending-lens-rethink.
Creates the required directory structure as per the implementation plan.
"""
import os
from pathlib import Path
import sys

def main():
    # Define the base project root relative to this script's location
    # Assuming this script is at: projects/PROJ-925-.../code/setup_project.py
    # We need to go up two levels to reach the project root
    script_path = Path(__file__).resolve()
    project_root = script_path.parent.parent

    # Define the required directories relative to the project root
    required_dirs = [
        "code/data",
        "code/tests",
        "code/utils",
        "code/models",
        "data/raw",
        "data/processed",
        "docs"
    ]

    created_count = 0
    existing_count = 0

    print(f"Initializing project structure at: {project_root}")

    for dir_path in required_dirs:
        full_path = project_root / dir_path
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {full_path}")
            created_count += 1
        else:
            existing_count += 1

    print(f"Project structure initialization complete. Created: {created_count}, Existing: {existing_count}")

    # Verification: List the created structure to stdout
    print("\nVerifying directory structure:")
    for dir_path in required_dirs:
        full_path = project_root / dir_path
        if full_path.exists():
            print(f"  [OK] {full_path.relative_to(project_root)}")
        else:
            print(f"  [FAIL] {full_path.relative_to(project_root)}")
            return 1

    return 0

if __name__ == "__main__":
    sys.exit(main())
