"""
Script to set up the required code directory structure.
Creates code/{dataset,symbolic,bes,analysis,utils} directories.
"""
import os
import sys
from pathlib import Path
from typing import List

PROJECT_ROOT = Path(__file__).resolve().parent.parent
CODE_DIR = PROJECT_ROOT / "code"

SUBDIRS: List[str] = ["dataset", "symbolic", "bes", "analysis", "utils"]

def setup_code_directories():
    """
    Create the required code directory structure.
    """
    directories: List[Path] = [CODE_DIR] + [CODE_DIR / subdir for subdir in SUBDIRS]
    
    for directory in directories:
        if not directory.exists():
            print(f"Creating directory: {directory}")
            directory.mkdir(parents=True, exist_ok=True)
        else:
            print(f"Directory already exists: {directory}")
        
        # Create __init__.py to make them packages
        init_file = directory / "__init__.py"
        if not init_file.exists():
            init_file.touch()
            print(f"Created __init__.py in {directory}")

def main():
    """
    Main entry point.
    """
    setup_code_directories()
    print("Code directory structure setup complete.")

if __name__ == "__main__":
    main()
