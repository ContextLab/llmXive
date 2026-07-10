"""
Setup script for creating project data directories.

This script ensures that the required directory structure for
raw and processed data exists.
"""

import os
from pathlib import Path

def main():
    """Create data directory structure."""
    project_root = Path(__file__).resolve().parent.parent

    # Define directories
    directories = [
        project_root / "data" / "raw",
        project_root / "data" / "processed",
        project_root / "output",
        project_root / "output" / "figures",
        project_root / "output" / "logs",
    ]

    # Create directories
    for dir_path in directories:
        dir_path.mkdir(parents=True, exist_ok=True)
        print(f"Created directory: {dir_path}")

    print("✓ Data directory structure ready.")

if __name__ == "__main__":
    main()