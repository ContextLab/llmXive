"""
Project setup and initialization.
"""
import os
from pathlib import Path
from config import get_path

def create_directories() -> None:
    """
    Create the standard project directory structure.
    """
    dirs = [
        "code",
        "data",
        "tests",
        "docs",
        "data/raw",
        "data/processed",
        "data/results"
    ]
    
    for d in dirs:
        path = get_path("CODE_DIR").parent / d
        path.mkdir(parents=True, exist_ok=True)
        print(f"Created directory: {path}")

def main():
    """
    Main entry point for setup.
    """
    create_directories()
    print("Project structure initialized.")

if __name__ == "__main__":
    main()