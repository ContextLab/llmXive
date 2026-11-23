"""
Directory setup utilities for the llmXive automated science pipeline.
This module ensures the required data directory structure exists.
"""
import os
from pathlib import Path
import sys

from config import get_project_root


def setup_data_directories():
    """
    Creates the required data directory structure:
    - data/raw/
    - data/processed/

    Returns:
        dict: A dictionary containing the Path objects for the created directories.
    """
    project_root = get_project_root()
    data_dir = project_root / "data"
    raw_dir = data_dir / "raw"
    processed_dir = data_dir / "processed"

    # Create directories if they don't exist
    raw_dir.mkdir(parents=True, exist_ok=True)
    processed_dir.mkdir(parents=True, exist_ok=True)

    return {
        "data": data_dir,
        "raw": raw_dir,
        "processed": processed_dir
    }


def main():
    """
    Main entry point for running the directory setup script directly.
    Creates the necessary directories and prints confirmation.
    """
    try:
        dirs = setup_data_directories()
        print(f"Successfully created directory structure at: {dirs['data']}")
        print(f"  - Raw data: {dirs['raw']}")
        print(f"  - Processed data: {dirs['processed']}")
        return 0
    except Exception as e:
        print(f"Error setting up directories: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
