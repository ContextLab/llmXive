import os
import sys
from pathlib import Path

def create_raw_data_directory():
    """Create raw data directory."""
    Path('data/raw').mkdir(parents=True, exist_ok=True)
    (Path('data/raw') / '.gitkeep').touch(exist_ok=True)
    print("Raw data directory created.")

def main():
    create_raw_data_directory()

if __name__ == "__main__":
    main()
