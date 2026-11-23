"""
Script to create the data directory for the project.
This script ensures the data directory exists at the specified path.
"""
import os
from pathlib import Path

def main():
    """Create the data directory if it does not exist."""
    # Determine the project root based on the known structure
    # The script is located at code/scripts/, so project root is two levels up
    script_dir = Path(__file__).resolve().parent
    code_dir = script_dir.parent
    project_root = code_dir.parent

    data_dir = code_dir / "data"

    if not data_dir.exists():
        data_dir.mkdir(parents=True, exist_ok=True)
        print(f"Created data directory: {data_dir}")
    else:
        print(f"Data directory already exists: {data_dir}")

    return 0

if __name__ == "__main__":
    exit(main())
