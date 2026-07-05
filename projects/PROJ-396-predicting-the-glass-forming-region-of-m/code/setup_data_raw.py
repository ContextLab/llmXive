"""
Script to create the data/raw/ directory for storing raw dataset files.
This directory is part of the standardized data structure for the glass-forming region project.
"""
import os
from pathlib import Path
from setup_directories import create_directory


def main():
    """Create the data/raw directory if it doesn't exist."""
    # Define the path relative to the project root
    raw_dir = Path("data/raw")
    
    # Create the directory using the shared helper
    create_directory(raw_dir)
    
    print(f"Successfully created directory: {raw_dir}")
    return 0


if __name__ == "__main__":
    exit(main())
