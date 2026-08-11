"""
Script to set up the project directory structure.

Creates the necessary directories for the project:
- src/
- tests/
- data/raw
- data/processed
- data/results
- logs
- figures
- contracts
"""

import os
from pathlib import Path

def main():
    """Create the project directory structure."""
    # Define directories relative to this script's location
    script_dir = Path(__file__).parent
    project_root = script_dir.parent

    directories = [
        project_root / "code" / "src",
        project_root / "code" / "tests",
        project_root / "code" / "data" / "raw",
        project_root / "code" / "data" / "processed",
        project_root / "code" / "data" / "results",
        project_root / "code" / "logs",
        project_root / "code" / "figures",
        project_root / "code" / "contracts",
        project_root / "code" / "specs",
    ]

    print("Creating project directory structure...")
    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)
        print(f"Created: {directory}")

    print("Directory structure setup complete!")

if __name__ == "__main__":
    main()