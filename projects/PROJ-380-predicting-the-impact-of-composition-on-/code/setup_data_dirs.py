"""
Script to initialize the project directory structure.
"""
import os
from pathlib import Path

from utils.config import get_paths, ensure_directories

def main():
    """Create all necessary directories for the project."""
    paths = get_paths()
    dirs_to_create = [
        paths["data_raw"],
        paths["data_processed"],
        paths["data_artifacts"],
        paths["state_projects"],
        paths["figures"],
        paths["contracts"],
        paths["specs"]
    ]
    ensure_directories(dirs_to_create)
    print(f"Created {len(dirs_to_create)} directories.")
    print(f"Project root: {paths['root']}")

if __name__ == "__main__":
    main()
