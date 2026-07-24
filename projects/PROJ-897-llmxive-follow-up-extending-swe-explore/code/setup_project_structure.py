import os
import sys
from pathlib import Path
from typing import List

def main():
    """Create the project directory structure."""
    root = Path(__file__).resolve().parent.parent
    
    required_dirs = [
        "code",
        "data/raw",
        "data/curated",
        "data/results",
        "tests/unit",
        "tests/contract",
        "contracts",
        "docs",
        "paper",
        "figures"
    ]
    
    for dir_path in directories:
        full_path = root / dir_path
        full_path.mkdir(parents=True, exist_ok=True)
        print(f"Created directory: {full_path}")
    
    print("Project structure created successfully.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
