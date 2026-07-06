"""
Script to create the data/processed/ directory.
This directory will store cleaned and processed datasets ready for modeling.
"""
import os
from pathlib import Path
from setup_directories import create_directory


def main():
    """Entry point to create the data/processed/ directory."""
    root_dir = Path(__file__).resolve().parent.parent
    data_dir = root_dir / "data"
    processed_dir = data_dir / "processed"

    create_directory(processed_dir)
    print(f"Successfully created directory: {processed_dir}")


if __name__ == "__main__":
    main()