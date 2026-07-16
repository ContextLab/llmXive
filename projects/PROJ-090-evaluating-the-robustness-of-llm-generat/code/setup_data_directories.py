"""
Data Directory Setup Script for PROJ-090.

This script creates the required directory structure for data storage:
- data/
  - raw/       (Original downloaded datasets, e.g., HumanEval)
  - processed/ (Perturbed variants, execution results, analysis outputs)
  - logs/      (Runtime logs, candidate pools, debug info)
- data/config/ (Configuration snapshots, feasibility reports)

Usage:
    python code/setup_data_directories.py
"""

import os
from pathlib import Path
from config import ensure_directories


def create_data_directories():
    """
    Create the standard data directory structure required by the project.

    Creates the following paths relative to the project root:
    - data/
    - data/raw/
    - data/processed/
    - data/logs/
    - data/config/

    Returns:
        Path: The root `data/` directory path.
    """
    base_dir = Path("data")
    directories = [
        base_dir,
        base_dir / "raw",
        base_dir / "processed",
        base_dir / "logs",
        base_dir / "config",
    ]

    for dir_path in directories:
        ensure_directories([dir_path])
        print(f"Created directory: {dir_path}")

    return base_dir


def main():
    """
    Entry point for the script.
    """
    print("Initializing data directory structure...")
    create_data_directories()
    print("Data directory setup complete.")


if __name__ == "__main__":
    main()