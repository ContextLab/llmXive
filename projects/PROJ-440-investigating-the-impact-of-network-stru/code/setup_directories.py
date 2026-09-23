"""
Setup script to create the required directory structure for the project.
"""
import os
from pathlib import Path

def setup_directories():
    """
    Creates the following directory structure:
    - code/
    - data/
    - data/raw/
    - data/processed/
    - data/analysis/
    - tests/
    - contracts/
    - state/
    """
    base_path = Path.cwd()
    
    directories = [
        "code",
        "data",
        "data/raw",
        "data/processed",
        "data/analysis",
        "tests",
        "contracts",
        "state"
    ]
    
    for dir_path in directories:
        full_path = base_path / dir_path
        full_path.mkdir(parents=True, exist_ok=True)
        print(f"Created directory: {full_path}")

if __name__ == "__main__":
    setup_directories()
