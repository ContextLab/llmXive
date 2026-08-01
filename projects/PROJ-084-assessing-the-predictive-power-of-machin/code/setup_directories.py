"""
Setup script to create project directories.
"""

import os
from pathlib import Path

def main():
    """Create all necessary project directories."""
    project_root = Path(__file__).resolve().parent.parent

    directories = [
        project_root / "code",
        project_root / "data" / "raw",
        project_root / "data" / "processed",
        project_root / "data" / "results",
        project_root / "tests"
    ]

    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)
        print(f"Created directory: {directory}")

    # Create __init__.py files
    for directory in directories:
        init_file = directory / "__init__.py"
        if not init_file.exists():
            init_file.touch()
            print(f"Created {init_file}")

    print("Directory setup complete.")

if __name__ == "__main__":
    main()
