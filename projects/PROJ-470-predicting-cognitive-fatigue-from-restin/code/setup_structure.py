import os
import sys
from pathlib import Path

def main():
    """
    Creates the required project directory structure for PROJ-470.
    This script ensures that the following directories exist relative to the project root:
    - data/raw
    - data/processed
    - data/analysis
    - code
    - tests/unit
    - tests/integration
    - docs
    """
    # Determine the project root.
    # We assume this script is run from the project root or the script is located in code/
    # and we want to create dirs relative to the parent of 'code'.
    script_path = Path(__file__).resolve()
    project_root = script_path.parent.parent

    # Define the required directories relative to project_root
    required_dirs = [
        "data/raw",
        "data/processed",
        "data/analysis",
        "code",
        "tests/unit",
        "tests/integration",
        "docs"
    ]

    created_count = 0
    existing_count = 0

    print(f"Project Root: {project_root}")

    for dir_path in required_dirs:
        full_path = project_root / dir_path
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            print(f"Created: {full_path}")
            created_count += 1
        else:
            print(f"Exists: {full_path}")
            existing_count += 1

    print(f"Directory structure setup complete. Created: {created_count}, Existing: {existing_count}")
    return 0

if __name__ == "__main__":
    sys.exit(main())