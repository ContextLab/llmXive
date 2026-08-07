"""
Directory Setup Script for PROJ-298.

This script creates the necessary directory structure for the project
as defined in plan.md. It ensures that data/raw, data/processed,
data/events, and data/taxonomy directories exist.

It does NOT create or write any data files (JSON, CSV, etc).
"""
import os
from pathlib import Path
import sys

def ensure_output_dir(path: Path) -> None:
    """Create directory if it does not exist."""
    if not path.exists():
        path.mkdir(parents=True, exist_ok=True)
        print(f"Created directory: {path}")
    else:
        print(f"Directory already exists: {path}")

def main() -> None:
    """Create the required directory structure."""
    # Determine project root relative to this script's location
    # Script is at code/setup_directories.py, so project root is two levels up
    script_dir = Path(__file__).resolve().parent
    project_root = script_dir.parent

    # Define required directories relative to project root
    required_dirs = [
        project_root / "data",
        project_root / "data" / "raw",
        project_root / "data" / "processed",
        project_root / "data" / "events",
        project_root / "data" / "taxonomy",
    ]

    print(f"Project root: {project_root}")
    print("Ensuring directory structure...")

    for dir_path in required_dirs:
        ensure_output_dir(dir_path)

    print("Directory setup complete.")

if __name__ == "__main__":
    main()