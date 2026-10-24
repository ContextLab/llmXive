"""
Script to create the required project scaffold directories.
This is used by the T001 test to ensure that the expected folders exist.
"""
import sys
from pathlib import Path

# Ensure the repository root is on the import path so we can import the scaffolding helper
sys.path.append(str(Path(__file__).resolve().parents[2]))

from scaffolding import create_project_structure

def main():
    create_project_structure()
    print("Project scaffold created.")

if __name__ == "__main__":
    main()