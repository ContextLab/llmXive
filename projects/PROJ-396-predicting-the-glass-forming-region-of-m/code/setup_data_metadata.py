import os
from pathlib import Path
from setup_directories import create_directory

def main():
    """Create the data/metadata directory if it does not exist."""
    root = Path.cwd()
    metadata_dir = root / "data" / "metadata"
    create_directory(metadata_dir)
    print(f"Created directory: {metadata_dir}")

if __name__ == "__main__":
    main()
