"""
Directory Setup Module.

Creates the necessary directory structure for the project.
"""

import os
import sys
from pathlib import Path

def create_directory_structure():
    """
    Create standard project directories.
    """
    dirs = [
        "data/raw",
        "data/processed",
        "code",
        "tests",
        "results",
        "logs",
        "contracts"
    ]
    
    for d in dirs:
        path = Path(d)
        path.mkdir(parents=True, exist_ok=True)
        print(f"Created directory: {path}")
        
    # Create __init__.py files if missing
    for d in ["code", "tests"]:
        init_file = Path(d) / "__init__.py"
        if not init_file.exists():
            init_file.touch()
            print(f"Created {init_file}")

if __name__ == "__main__":
    create_directory_structure()
