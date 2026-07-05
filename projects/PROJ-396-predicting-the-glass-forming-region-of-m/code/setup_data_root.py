import os
from pathlib import Path
from setup_directories import create_directory

def main():
    """Create the root 'data' directory at the repository root."""
    root = Path(__file__).resolve().parent.parent
    data_dir = root / "data"
    create_directory(data_dir)
    print(f"Created directory: {data_dir}")

if __name__ == "__main__":
    main()
