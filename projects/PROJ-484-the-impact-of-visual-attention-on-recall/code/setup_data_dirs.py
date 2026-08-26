"""
Script to create the required data directory structure for the project.
This ensures all necessary folders exist before data processing begins.
"""
import os
import sys
from pathlib import Path

def main():
    """Create the project data directory structure."""
    # Define the project root relative to this script's location
    # The script is in code/, so root is one level up
    script_dir = Path(__file__).parent
    project_root = script_dir.parent

    # Define the directories to create relative to project root
    # Based on tasks.md and standard project layout
    directories = [
        "data/raw",
        "data/processed",
        "artifacts/figures",
        "artifacts/logs"
    ]

    created_count = 0
    existing_count = 0

    for dir_path in directories:
        full_path = project_root / dir_path
        try:
            full_path.mkdir(parents=True, exist_ok=True)
            if full_path.is_dir():
                print(f"Created (or verified): {full_path}")
                created_count += 1
            else:
                print(f"ERROR: Path exists but is not a directory: {full_path}")
                sys.exit(1)
        except PermissionError:
            print(f"ERROR: Permission denied creating directory: {full_path}")
            sys.exit(1)
        except Exception as e:
            print(f"ERROR: Failed to create directory {full_path}: {e}")
            sys.exit(1)

    print(f"\nDirectory setup complete. Created/verified {created_count} directories.")
    print(f"Project root: {project_root}")

    # Verify structure
    print("\nVerifying structure:")
    for dir_path in directories:
        full_path = project_root / dir_path
        if full_path.exists():
            print(f"  [OK] {dir_path}")
        else:
            print(f"  [FAIL] {dir_path}")
            sys.exit(1)

    return 0

if __name__ == "__main__":
    sys.exit(main())