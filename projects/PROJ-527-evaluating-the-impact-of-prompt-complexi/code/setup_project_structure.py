"""
Main entry point for setting up the full project structure.
This script orchestrates the creation of all necessary directories.
"""
import os
from pathlib import Path
from setup_data_directories import create_data_directories

def main():
    """Main entry point for project setup."""
    print("Setting up project structure...")
    created = create_data_directories()
    print("Project structure setup complete.")
    return 0

if __name__ == "__main__":
    exit(main())
