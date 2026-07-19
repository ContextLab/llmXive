"""
Script to create the required project directory structure.
This implements task T001a.
"""
import os
import sys
from pathlib import Path

def ensure_directory(dir_path: Path) -> None:
    """Create directory if it does not exist."""
    if not dir_path.exists():
        dir_path.mkdir(parents=True, exist_ok=True)
        print(f"Created directory: {dir_path}")
    else:
        print(f"Directory already exists: {dir_path}")

def main() -> None:
    """Create all required directories for the project."""
    # Define the project root relative to where this script is run
    # Assuming the script is run from the project root
    project_root = Path.cwd()

    # Define required directories
    directories = [
        project_root / "data" / "raw",
        project_root / "data" / "processed",
        project_root / "code",
        project_root / "tests",
        project_root / "results",
        project_root / "projects" / "PROJ-967-llmxive-follow-up-extending-beyond-scala",
    ]

    print(f"Setting up directory structure in: {project_root}")
    for dir_path in directories:
        ensure_directory(dir_path)

    print("Directory setup complete.")

if __name__ == "__main__":
    main()