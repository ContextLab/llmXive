"""
Directory Setup for Statistical Analysis of Stack Overflow Tags.
Creates the required directory structure for data artifacts as per plan.md.
Does NOT write any data files; only ensures directories exist.
"""
import os
from pathlib import Path
import sys

# Project root relative to this script's location
# Script is at code/setup_data_structure.py, so root is two levels up
PROJECT_ROOT = Path(__file__).resolve().parent.parent

def ensure_output_dir(dir_path: Path) -> None:
    """Create directory if it does not exist."""
    if not dir_path.exists():
        dir_path.mkdir(parents=True, exist_ok=True)
        print(f"Created directory: {dir_path}")
    else:
        print(f"Directory already exists: {dir_path}")

def main() -> None:
    """Create the required data directory structure."""
    print(f"Project Root: {PROJECT_ROOT}")
    
    # Define the required data directories based on plan.md structure
    # T008 specifically requests: data/, data/raw/, data/processed/, data/events/, data/taxonomy/
    data_dirs = [
        PROJECT_ROOT / "data",
        PROJECT_ROOT / "data" / "raw",
        PROJECT_ROOT / "data" / "processed",
        PROJECT_ROOT / "data" / "events",
        PROJECT_ROOT / "data" / "taxonomy",
    ]

    for dir_path in data_dirs:
        ensure_output_dir(dir_path)

    print("Directory setup complete.")

if __name__ == "__main__":
    main()
