"""
Script to create the required data directory structure for the project.
Implements Task T001a.
"""
import os
import sys
from pathlib import Path

def create_directories():
    """
    Creates the directory hierarchy defined in docs/design/directory_structure.md.
    """
    # Determine project root (assuming script is in code/scripts/)
    script_dir = Path(__file__).resolve().parent
    project_root = script_dir.parent.parent
    data_root = project_root / "data"

    directories = [
        "raw",
        "derived/topology",
        "derived/vdos",
        "derived/reference",
        "derived/correlation",
        "metadata"
    ]

    created_count = 0
    for dir_name in directories:
        full_path = data_root / dir_name
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {full_path}")
            created_count += 1
        else:
            print(f"Directory already exists: {full_path}")

    print(f"\nSetup complete. {created_count} new directories created.")
    return True

def main():
    success = create_directories()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
