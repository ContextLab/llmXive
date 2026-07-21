"""
Script to initialize the project structure.
"""
import os
import sys
from pathlib import Path


def main():
    """Create the required project directories."""
    base_dir = Path(__file__).parent
    directories = [
        "src/brainnet",
        "tests/unit",
        "tests/contract",
        "data/processed",
        "data/raw",
        "results/figures",
        "metadata",
        "contracts"
    ]
    
    for dir_path in directories:
        full_path = base_dir / dir_path
        full_path.mkdir(parents=True, exist_ok=True)
        print(f"Created: {full_path}")
        
    print("Project structure initialized successfully.")


if __name__ == "__main__":
    main()