"""
Setup script for project directories.
Creates the necessary folder structure.
"""
import os
from pathlib import Path
from utils.config import get_path, ensure_dirs_exist

def main():
    """
    Creates all required directories.
    """
    ensure_dirs_exist()
    print("Project directories created successfully.")

if __name__ == "__main__":
    main()