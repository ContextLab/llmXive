"""
Setup script to initialize the project directory structure for glass transition
temperature prediction research.

Creates the following directories relative to the project root:
- data/raw: For downloaded raw datasets (e.g., from NIST/Zenodo)
- data/processed: For featurized and cleaned datasets
- artifacts: For trained models, reports, and intermediate results
- state: For pipeline state tracking and checkpoints

This script is idempotent; running it multiple times will not raise errors
if directories already exist.
"""

import os
from pathlib import Path


def main():
    """
    Create the required directory structure for the glass transition prediction project.

    Directories created:
    - data/raw
    - data/processed
    - artifacts
    - state

    Returns:
        None
    """
    # Determine project root (parent of the 'code' directory)
    current_file = Path(__file__).resolve()
    project_root = current_file.parent.parent

    # Define relative directory paths
    directories = [
        project_root / "data" / "raw",
        project_root / "data" / "processed",
        project_root / "artifacts",
        project_root / "state",
    ]

    # Create directories
    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)
        print(f"Created directory: {directory}")

    print("Directory setup complete.")


if __name__ == "__main__":
    main()