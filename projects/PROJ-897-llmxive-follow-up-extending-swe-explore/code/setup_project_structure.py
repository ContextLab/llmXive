"""
Setup script to initialize the llmXive project directory structure.
Creates the required directories for code, data, tests, contracts, docs, and paper.
"""
import os
import sys
from pathlib import Path

def main():
    """Create the project directory structure."""
    root = Path(".")
    
    directories = [
        "code",
        "data/raw",
        "data/curated",
        "data/results",
        "tests/unit",
        "tests/contract",
        "contracts",
        "docs",
        "paper",
    ]
    
    created = []
    for d in directories:
        path = root / d
        if not path.exists():
            path.mkdir(parents=True, exist_ok=True)
            created.append(str(path))
            print(f"Created directory: {path}")
        else:
            print(f"Directory already exists: {path}")
    
    if not created:
        print("All required directories already exist.")
    else:
        print(f"\nSuccessfully created {len(created)} directories.")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())