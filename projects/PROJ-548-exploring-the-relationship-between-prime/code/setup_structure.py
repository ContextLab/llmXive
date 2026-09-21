import os
import sys
from pathlib import Path

def main():
    """
    Create the project directory structure for PROJ-548.
    Ensures all required folders exist relative to the project root.
    """
    # Define the project root (assumed to be the parent of the 'code' directory)
    # Since this script is in 'code/', we go up one level to find the root.
    script_path = Path(__file__).resolve()
    project_root = script_path.parent.parent

    # Define required directories relative to project root
    required_dirs = [
        "src/data",
        "src/analysis",
        "src/utils",
        "src/cli",
        "tests/unit",
        "tests/integration",
        "data/raw",
        "data/processed",
        "data/results",
        "results",
        "state",
    ]

    created_count = 0
    existing_count = 0

    print(f"Project root detected at: {project_root}")
    print("Ensuring directory structure...")

    for dir_path in required_dirs:
        full_path = project_root / dir_path
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            print(f"  Created: {full_path.relative_to(project_root)}")
            created_count += 1
        else:
            print(f"  Exists:  {full_path.relative_to(project_root)}")
            existing_count += 1

    print(f"\nSetup complete. Created {created_count} directories, found {existing_count} existing.")
    return 0

if __name__ == "__main__":
    sys.exit(main())