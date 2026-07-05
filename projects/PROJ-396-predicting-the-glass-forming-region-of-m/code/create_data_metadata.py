import os
from pathlib import Path
from setup_directories import create_directory

def main():
    """Create the data/metadata directory for storing descriptor sources and configuration."""
    base_dir = Path(__file__).resolve().parent.parent
    metadata_dir = base_dir / "data" / "metadata"
    create_directory(metadata_dir)
    print(f"Created directory: {metadata_dir}")

if __name__ == "__main__":
    main()