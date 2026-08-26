"""
Script to initialize project directory structure.
Implements T001 logic explicitly.
"""
import os
from pathlib import Path
from config import ensure_directories

def main():
    """
    Entry point to create project directories and __init__.py files.
    """
    print("Initializing project directories...")
    success = ensure_directories()
    if success:
        print("Project directories created successfully.")
    else:
        print("Failed to create directories.")
        return 1
    return 0

if __name__ == "__main__":
    exit(main())
