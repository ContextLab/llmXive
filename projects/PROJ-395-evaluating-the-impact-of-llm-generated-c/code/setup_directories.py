"""
Setup Directories Script
-------------------------

This script creates the required directory hierarchy for the project:

- data/
  - raw/
  - processed/
- state/
- code/

It is safe to run multiple times; existing directories are left untouched.
"""

import os
from pathlib import Path

def create_directory(path: Path) -> None:
    """
    Create a directory (including parents) if it does not already exist.

    Args:
        path: Path object representing the directory to create.
    """
    try:
        path.mkdir(parents=True, exist_ok=True)
        print(f"Created (or already exists): {path}")
    except Exception as exc:
        # Re‑raise to make the script fail loudly on unexpected errors
        raise RuntimeError(f"Failed to create directory {path}: {exc}") from exc

def main() -> None:
    """
    Entry point: ensure the project sub‑directories exist.

    The script assumes it is executed from the project root (the directory
    that contains the top‑level ``code`` folder). All paths are resolved
    relative to the current working directory.
    """
    # Define the required directories relative to the project root
    required_dirs = [
        Path("data/raw"),
        Path("data/processed"),
        Path("state"),
        Path("code"),
    ]

    for dir_path in required_dirs:
        create_directory(dir_path)

    print("All required directories are now present.")

if __name__ == "__main__":
    main()
