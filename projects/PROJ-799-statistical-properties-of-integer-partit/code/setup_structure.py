import os
import sys
from pathlib import Path

def main():
    """
    Creates the complete directory structure for project PROJ-799.
    This script is idempotent and safe to run multiple times.
    """
    project_root = Path(__file__).resolve().parent.parent
    project_name = "PROJ-799-statistical-properties-of-integer-partit"
    base_dir = project_root / project_name

    # Define the required directory structure relative to base_dir
    directories = [
        "code",
        "code/utils",
        "data/raw",
        "data/processed",
        "data/schemas",
        "tests",
        "tests/data",
        "docs",
        "state",
        "state/projects",
    ]

    print(f"Ensuring directory structure for {project_name}...")
    for dir_path in directories:
        full_path = base_dir / dir_path
        full_path.mkdir(parents=True, exist_ok=True)
        print(f"  Created/Verified: {full_path.relative_to(project_root)}")

    print("Directory structure setup complete.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
