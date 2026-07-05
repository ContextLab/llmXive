"""
Script to initialize the data directory structure and generate initial checksums.
This script creates the required subdirectories and prepares the environment for data acquisition.
"""
import os
import sys
from pathlib import Path

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from code.config import DATA_DIR
from code.data.checksum import generate_checksums, save_checksums


def create_structure():
    """Create the required data directory structure."""
    subdirs = ["raw", "curated", "artifacts", "logs", "errors"]
    created = []

    for subdir in subdirs:
        path = DATA_DIR / subdir
        path.mkdir(parents=True, exist_ok=True)
        created.append(path)
        print(f"Created: {path}")

    return created


def main():
    """Main entry point for data directory setup."""
    print(f"Data directory base: {DATA_DIR}")

    if not DATA_DIR.exists():
        DATA_DIR.mkdir(parents=True)
        print(f"Created base data directory: {DATA_DIR}")

    created_dirs = create_structure()

    # Generate initial checksums (empty state)
    checksums = generate_checksums(DATA_DIR)
    save_checksums(checksums)
    print(f"Initialized checksums file at {DATA_DIR / 'checksums.json'}")

    print("\nData directory structure ready.")
    print(f"  - {DATA_DIR / 'raw'}      : Raw downloaded data")
    print(f"  - {DATA_DIR / 'curated'}   : Processed/cleaned data")
    print(f"  - {DATA_DIR / 'artifacts'} : Model artifacts and intermediate results")
    print(f"  - {DATA_DIR / 'logs'}      : Execution logs")
    print(f"  - {DATA_DIR / 'errors'}    : Error reports and exclusion logs")


if __name__ == "__main__":
    main()