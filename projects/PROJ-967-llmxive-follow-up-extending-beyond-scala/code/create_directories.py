import os
import sys
from pathlib import Path
import logging

def ensure_directory(path: str) -> None:
    """
    Ensures that a directory exists.

    Args:
        path: The path to the directory.
    """
    Path(path).mkdir(parents=True, exist_ok=True)

def main():
    """
    Creates the project directory structure.
    """
    project_root = "projects/PROJ-967-llmxive-follow-up-extending-beyond-scala"
    directories = [
        f"{project_root}/data/raw",
        f"{project_root}/data/processed",
        f"{project_root}/results",
        f"{project_root}/code",
        f"{project_root}/tests",
    ]

    for directory in directories:
        ensure_directory(directory)
        logging.info(f"Created directory: {directory}")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
