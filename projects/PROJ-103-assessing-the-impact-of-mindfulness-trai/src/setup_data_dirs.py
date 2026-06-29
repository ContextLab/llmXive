#!/usr/bin/env python3
"""
Setup script to create the data directory structure for the mindfulness-DMN study.
Creates data/raw/, data/processed/, and data/results/ directories with __init__.py files.
"""

import os
from pathlib import Path


def create_data_directories():
    """Create the data directory structure for the project."""
    # Get the project root (parent of src/ directory where this script lives)
    script_dir = Path(__file__).parent.resolve()
    project_root = script_dir.parent

    # Define the data directories to create
    data_dirs = [
        project_root / "data" / "raw",
        project_root / "data" / "processed",
        project_root / "data" / "results",
    ]

    # Create each directory
    for dir_path in data_dirs:
        dir_path.mkdir(parents=True, exist_ok=True)
        print(f"Created: {dir_path}")

        # Create __init__.py in each subdirectory
        init_file = dir_path / "__init__.py"
        init_file.write_text("")
        print(f"Created: {init_file}")

    # Create __init__.py in the main data directory
    data_root = project_root / "data"
    data_root.mkdir(parents=True, exist_ok=True)
    init_file = data_root / "__init__.py"
    init_file.write_text("")
    print(f"Created: {init_file}")

    print("\nData directory structure created successfully!")
    print(f"Project root: {project_root}")
    print(f"Data directory: {data_root}")


if __name__ == "__main__":
    create_data_directories()