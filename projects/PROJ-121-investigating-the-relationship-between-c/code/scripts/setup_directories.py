"""
Script to initialize the project directory structure.
Creates required folders for data, reports, and source code.
"""
import os
import sys
from pathlib import Path

def main():
    """Create the standard directory structure for the project."""
    # Define the project root relative to this script's location
    # The script is in code/scripts/, so root is two levels up
    script_dir = Path(__file__).resolve().parent
    project_root = script_dir.parent.parent

    # Define relative paths as per task requirements
    # Note: The task asks for 'code/src', but our structure is 'code/src'
    # We will create directories relative to the project root.
    # Based on existing API surface, 'code/src' exists.
    # We need to ensure 'data' subfolders and 'reports' exist.
    
    directories = [
        "data/raw",
        "data/processed",
        "data/results",
        "reports",
        # Ensure code/src exists if not already (it is referenced in imports)
        "code/src", 
        "code/tests",
        "code/tests/unit",
        "code/tests/contract",
        "code/tests/integration",
        "code/scripts",
        "figures",
        "data/synthetic"
    ]

    created_count = 0
    skipped_count = 0

    for dir_path in directories:
        full_path = project_root / dir_path
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {full_path.relative_to(project_root)}")
            created_count += 1
        else:
            skipped_count += 1

    print(f"Directory setup complete. Created: {created_count}, Skipped: {skipped_count}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
