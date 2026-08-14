"""
Setup script to create the project directory structure for PROJ-269.
This script ensures all required folders exist under the project root.
"""
import os
from pathlib import Path

def main():
    # Define the project root relative to the script location
    # Assuming this script is run from the project root or installed in the repo
    # We use the parent of the 'code' directory as the project root.
    script_path = Path(__file__).resolve()
    project_root = script_path.parent.parent

    # Define the required directories relative to the project root
    required_dirs = [
        "code",
        "data/raw",
        "data/derived",
        "results",
        "tests",
        "contracts"
    ]

    created_count = 0
    for dir_name in required_dirs:
        full_path = project_root / dir_name
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {full_path}")
            created_count += 1
        else:
            print(f"Directory already exists: {full_path}")

    print(f"\nSetup complete. Created {created_count} new directories.")
    print(f"Project root: {project_root}")

    # Verify structure
    print("\nVerifying directory structure:")
    for dir_name in required_dirs:
        full_path = project_root / dir_name
        if full_path.exists() and full_path.is_dir():
            print(f"  [OK] {dir_name}")
        else:
            print(f"  [FAIL] {dir_name}")

if __name__ == "__main__":
    main()
