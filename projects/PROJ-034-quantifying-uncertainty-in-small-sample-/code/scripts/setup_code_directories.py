import os
import sys
from pathlib import Path

def create_directories():
    """
    Creates the required directory structure for the code/ module.
    Directories created:
    - code/simulation
    - code/models
    - code/metrics
    - code/validation
    - code/plots
    - code/scripts
    """
    base_path = Path(__file__).resolve().parent.parent
    directories = [
        "simulation",
        "models",
        "metrics",
        "validation",
        "plots",
        "scripts"
    ]

    created_count = 0
    for dirname in directories:
        dir_path = base_path / dirname
        if not dir_path.exists():
            dir_path.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {dir_path}")
            created_count += 1
        else:
            print(f"Directory already exists: {dir_path}")

    print(f"Total directories created: {created_count}")
    return created_count

def main():
    """Entry point for script execution."""
    create_directories()
    return 0

if __name__ == "__main__":
    sys.exit(main())