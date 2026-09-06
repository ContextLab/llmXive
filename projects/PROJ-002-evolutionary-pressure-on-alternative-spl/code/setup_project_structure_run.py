"""
Entry point to execute the project structure creation.
This script is run to ensure T001a is satisfied by physically creating the directories.
"""
import sys
import os
from pathlib import Path

# Ensure the code directory is in the path for imports
current_dir = Path(__file__).parent
if str(current_dir) not in sys.path:
    sys.path.insert(0, str(current_dir))

from setup_project_structure import create_directories

def main():
    print("Running T001a: Creating project directory structure...")
    create_directories(".")
    print("T001a execution complete.")

if __name__ == "__main__":
    main()