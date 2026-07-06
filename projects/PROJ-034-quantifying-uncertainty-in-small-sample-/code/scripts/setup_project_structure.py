import os
import sys
from pathlib import Path

def create_directories():
    """Create the project directory structure as per implementation plan."""
    # Define all required directories relative to project root
    # Assuming this script is run from the project root or code/scripts
    base_path = Path(__file__).parent.parent.parent  # Go up from code/scripts to root

    directories = [
        "code/simulation",
        "code/models",
        "code/metrics",
        "code/validation",
        "code/plots",
        "code/scripts",
        "data/raw",
        "data/simulated",
        "data/results",
        "tests/unit",
        "tests/integration",
        "docs/paper",
    ]

    created_count = 0
    for dir_path in directories:
        full_path = base_path / dir_path
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {full_path}")
            created_count += 1
        else:
            print(f"Directory already exists: {full_path}")

    # Create .gitkeep files in data directories to ensure they are tracked
    data_dirs = [
        "data/raw",
        "data/simulated",
        "data/results",
    ]
    for dir_path in data_dirs:
        full_path = base_path / dir_path
        gitkeep_path = full_path / ".gitkeep"
        if not gitkeep_path.exists():
            gitkeep_path.touch()
            print(f"Created .gitkeep in: {full_path}")
            created_count += 1

    print(f"\nTotal directories/files created: {created_count}")
    return True

def main():
    """Entry point for the script."""
    success = create_directories()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()