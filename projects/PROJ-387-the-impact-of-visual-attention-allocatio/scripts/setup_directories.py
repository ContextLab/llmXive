"""
Script to ensure the base directory structure exists.
Run this if the project is cloned and directories are missing.
"""
import os
from pathlib import Path
from utils.directories import create_base_directory_structure

def main():
    root = Path(__file__).parent.parent
    os.chdir(root)
    create_base_directory_structure()
    print("Directory structure created/verified.")

if __name__ == "__main__":
    main()