"""
Task T001a: Create project directories.

Creates the required directory structure for the llmXive follow-up project:
- data/raw
- data/processed
- code
- tests
- results

This script ensures all necessary folders exist relative to the project root.
"""
import os
import sys
from pathlib import Path

def ensure_directory(path: Path) -> None:
    """Ensure a directory exists, creating it if necessary."""
    if not path.exists():
        path.mkdir(parents=True, exist_ok=True)
        print(f"Created directory: {path}")
    else:
        print(f"Directory already exists: {path}")

def main() -> None:
    """Main entry point for directory creation."""
    # Determine project root relative to this script's location
    script_dir = Path(__file__).resolve().parent
    project_root = script_dir.parent  # projects/PROJ-967-llmxive-follow-up-extending-beyond-scala/

    # Define required directories relative to project root
    required_dirs = [
        "data/raw",
        "data/processed",
        "code",
        "tests",
        "results"
    ]

    print(f"Project root: {project_root}")
    print(f"Creating directories in: {project_root}")

    for dir_name in required_dirs:
        dir_path = project_root / dir_name
        ensure_directory(dir_path)

    print("Directory creation complete.")

if __name__ == "__main__":
    main()
