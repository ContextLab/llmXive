"""
Script to initialize the project directory structure for PROJ-521.
Creates required folders for code, data, tests, and outputs.
"""
import os
from pathlib import Path

def main():
    # Define the project root relative to where this script is run
    # Assuming this script is run from the project root or the parent of 'projects'
    # We will construct the path relative to the script's location to be safe.
    script_dir = Path(__file__).parent.resolve()
    project_root = script_dir / "projects" / "PROJ-521-the-impact-of-linguistic-complexity-on-t"

    # Define the required directory structure
    directories = [
        "code",
        "data/raw",
        "data/processed",
        "data/outputs/figures",
        "tests/unit",
        "tests/integration",
        "tests/contract",
    ]

    # Create directories
    created_count = 0
    for dir_name in directories:
        full_path = project_root / dir_name
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            print(f"Created: {full_path}")
            created_count += 1
        else:
            print(f"Exists: {full_path}")

    print(f"\nSetup complete. {created_count} new directories created.")

if __name__ == "__main__":
    main()
