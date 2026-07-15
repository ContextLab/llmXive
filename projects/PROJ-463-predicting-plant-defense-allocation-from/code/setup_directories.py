"""
Script to initialize the project directory structure.
"""
import os
import sys
from pathlib import Path

def main():
    """Create the required directory structure."""
    # Define project root relative to this script's location
    project_root = Path(__file__).resolve().parent
    
    # Define directories to create
    directories = [
        project_root / "src",
        project_root / "src" / "utils",
        project_root / "src" / "data",
        project_root / "src" / "analysis",
        project_root / "src" / "cli",
        project_root / "tests",
        project_root / "tests" / "unit",
        project_root / "tests" / "integration",
        project_root / "tests" / "contract",
        project_root / "data",
        project_root / "data" / "raw",
        project_root / "data" / "processed",
        project_root / "data" / "traits",
        project_root / "data" / "manifests",
        project_root / "data" / "synthetic",
        project_root / "figures",
        project_root / "specs",
    ]

    created_count = 0
    for directory in directories:
        if not directory.exists():
            directory.mkdir(parents=True, exist_ok=True)
            print(f"Created: {directory.relative_to(project_root)}")
            created_count += 1
        else:
            print(f"Exists:  {directory.relative_to(project_root)}")

    print(f"\nTotal directories created: {created_count}")
    print(f"Project root: {project_root}")

if __name__ == "__main__":
    main()