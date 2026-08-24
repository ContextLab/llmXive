"""
Setup script to initialize the project directory structure.
Creates code/, tests/, data/, and results/ directories at the repository root.
"""
import os
import sys
from pathlib import Path

def main():
    # Determine the project root (parent of the code/ directory where this script lives)
    # If run from code/, go up one level. If run from root, stay.
    current_file = Path(__file__).resolve()
    if current_file.parent.name == "code":
        project_root = current_file.parent.parent
    else:
        project_root = current_file.parent

    # Define required directories relative to project root
    required_dirs = [
        "code",
        "tests",
        "data",
        "results"
    ]

    created_count = 0
    for dir_name in required_dirs:
        dir_path = project_root / dir_name
        if not dir_path.exists():
            dir_path.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {dir_path}")
            created_count += 1
        else:
            print(f"Directory already exists: {dir_path}")

    print(f"\nSetup complete. {created_count} new directories created.")
    return 0

if __name__ == "__main__":
    sys.exit(main())