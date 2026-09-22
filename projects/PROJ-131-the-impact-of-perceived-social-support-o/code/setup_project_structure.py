"""
Project Setup Script.

Creates the directory structure for the project.
"""
import os
from pathlib import Path

def create_directories():
    """Creates the standard project directories."""
    base = Path(__file__).parent.parent
    dirs = [
        "code/data",
        "code/analysis",
        "code/config",
        "code/tests",
        "data/raw",
        "data/results",
        "data/figures",
        "specs/001-social-support-resilience"
    ]
    for d in dirs:
        (base / d).mkdir(parents=True, exist_ok=True)
        print(f"Created: {base / d}")

def main():
    create_directories()
    print("Project structure created.")

if __name__ == "__main__":
    main()
