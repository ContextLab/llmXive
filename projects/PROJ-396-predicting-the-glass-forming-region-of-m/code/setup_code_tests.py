"""
Setup script to create the code/tests/ directory structure.
"""
import os
from pathlib import Path
from setup_directories import create_directory

def main():
    """
    Creates the code/tests/ directory.
    """
    root_dir = Path.cwd()
    tests_dir = root_dir / "code" / "tests"
    
    # Ensure parent 'code' directory exists if not already
    code_dir = root_dir / "code"
    if not code_dir.exists():
        code_dir.mkdir(parents=True, exist_ok=True)
    
    create_directory(tests_dir)
    print(f"Directory created: {tests_dir}")

if __name__ == "__main__":
    main()
