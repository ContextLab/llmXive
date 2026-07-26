"""
Script to initialize the data directory structure for the llmXive project.

This script creates the necessary directories under `data/` to support:
- data/raw/: For raw downloaded datasets (e.g., COCO-Stuff, ParaDLC-Bench)
- data/synthetic/: For generated synthetic images and annotations
- data/processed/: For inference results, metrics, and regression outputs

It relies on `code/config.py` for path definitions and directory creation logic.
"""
import sys
from pathlib import Path

# Add parent directory to path to allow importing config
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import ensure_directories

def main():
    """
    Main entry point to setup the data directory structure.
    
    Reads configuration from config.py and creates the required directories.
    Prints status for each directory created.
    """
    print("Initializing data directory structure...")
    
    # The ensure_directories function in config.py handles the creation
    # of data/raw, data/synthetic, and data/processed based on the config.
    success = ensure_directories()
    
    if success:
        print("Data directory structure successfully created.")
        print("Directories:")
        print("  - data/raw/")
        print("  - data/synthetic/")
        print("  - data/processed/")
    else:
        print("Failed to create data directories.")
        sys.exit(1)

if __name__ == "__main__":
    main()
