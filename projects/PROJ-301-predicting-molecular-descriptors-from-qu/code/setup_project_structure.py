import os
import sys
from pathlib import Path

def create_directory(path: Path) -> None:
    """
    Create a directory if it doesn't exist.

    Args:
        path: Path to the directory.
    """
    path.mkdir(parents=True, exist_ok=True)

def main() -> None:
    """
    Main function to create the project structure.
    """
    directories = [
        Path("code"),
        Path("data/raw"),
        Path("data/processed"),
        Path("data/results"),
        Path("tests"),
        Path("utils"),
        Path("artifacts/models"),
        Path("artifacts/metrics"),
        Path("artifacts/plots"),
        Path("docs")
    ]

    for directory in directories:
        create_directory(directory)
        print(f"Created directory: {directory}")

if __name__ == "__main__":
    main()
