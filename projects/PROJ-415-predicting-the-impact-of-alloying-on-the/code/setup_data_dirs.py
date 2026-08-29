import os
import sys
from pathlib import Path
from typing import List

from config import DATA_DIR, PROJECT_ROOT, LOG_DIR, ERRORS_DIR


def create_directories() -> None:
    """Create the required data directory structure."""
    # Main data directories
    data_dirs = [
        DATA_DIR,
        DATA_DIR / "raw",
        DATA_DIR / "curated",
        DATA_DIR / "artifacts",
    ]
    
    # Additional required directories
    other_dirs = [
        LOG_DIR,
        ERRORS_DIR,
    ]
    
    all_dirs: List[Path] = data_dirs + other_dirs
    
    for dir_path in all_dirs:
        dir_path.mkdir(parents=True, exist_ok=True)
        print(f"Created directory: {dir_path}")


def create_init_files() -> None:
    """Create __init__.py files in data directories to make them Python packages."""
    init_dirs = [
        DATA_DIR,
        DATA_DIR / "raw",
        DATA_DIR / "curated",
        DATA_DIR / "artifacts",
    ]
    
    for dir_path in init_dirs:
        init_file = dir_path / "__init__.py"
        init_file.touch(exist_ok=True)
        print(f"Created __init__.py in {dir_path}")


def main() -> None:
    """Main entry point for data directory setup."""
    print("Setting up data directory structure...")
    create_directories()
    create_init_files()
    print("Data directory setup complete.")


if __name__ == "__main__":
    main()
