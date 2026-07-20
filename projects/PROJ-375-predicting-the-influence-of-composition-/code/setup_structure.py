"""
Project structure setup.
"""
import os
import sys
from pathlib import Path

def create_directories():
    """
    Create the required project directories.
    """
    directories = [
        "code/ingestion",
        "code/features",
        "code/modeling",
        "code/utils",
        "data/raw",
        "data/processed",
        "tests/unit",
        "tests/integration",
        "docs",
        "logs",
        "models",
        "results",
        "figures"
    ]

    for dir_path in directories:
        Path(dir_path).mkdir(parents=True, exist_ok=True)
        print(f"Created directory: {dir_path}")

if __name__ == "__main__":
    create_directories()
