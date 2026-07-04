"""
Script to create the project directory structure for PROJ-710.
This script ensures all required directories exist relative to the project root.
"""
import os
from pathlib import Path

def main():
    # Define the project root relative to this script's location
    # The script is in code/, so project root is one level up
    current_file = Path(__file__).resolve()
    code_dir = current_file.parent
    project_root = code_dir.parent

    # Define required directories relative to project root
    required_dirs = [
        "code",
        "code/data",
        "code/analysis",
        "code/utils",
        "code/tests",
        "artifacts"
    ]

    created_count = 0
    for dir_path in required_dirs:
        full_path = project_root / dir_path
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {full_path}")
            created_count += 1
        else:
            print(f"Directory exists: {full_path}")

    print(f"\nProject structure setup complete. {created_count} new directories created.")
    print(f"Project root: {project_root}")

if __name__ == "__main__":
    main()