import os
import sys
from pathlib import Path

def create_data_directories():
    """Create data subdirectories."""
    data_dirs = ['data/raw', 'data/processed', 'data/synthetic']
    for d in data_dirs:
        Path(d).mkdir(parents=True, exist_ok=True)
        (Path(d) / '.gitkeep').touch(exist_ok=True)
    print("Data directories created.")

def main():
    create_data_directories()

if __name__ == "__main__":
    main()
