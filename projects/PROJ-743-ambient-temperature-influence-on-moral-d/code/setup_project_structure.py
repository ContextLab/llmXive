"""
Project Structure Setup Module.

Creates the required directory structure for the llmXive project:
- code/
- data/raw/
- data/processed/
- results/figures/
- results/logs/
- results/stats/
- tests/
"""

import os
import sys
from pathlib import Path

# Define the required directories relative to the project root
REQUIRED_DIRS = [
    "code",
    "data/raw",
    "data/processed",
    "results/figures",
    "results/logs",
    "results/stats",
    "tests",
]


def ensure_directories(root_path: Path) -> None:
    """
    Creates all required directories if they do not already exist.

    Args:
        root_path: The root directory of the project (e.g., projects/PROJ-743-...).
    """
    for dir_name in REQUIRED_DIRS:
        dir_path = root_path / dir_name
        if not dir_path.exists():
            dir_path.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {dir_path}")
        else:
            # Verify it is a directory, not a file
            if not dir_path.is_dir():
                raise RuntimeError(f"Path exists but is not a directory: {dir_path}")


def main() -> None:
    """
    Entry point for the script.
    Determines the project root based on the current working directory
    and ensures all required directories exist.
    """
    # Assume the script is run from the project root
    root_path = Path.cwd()

    print(f"Setting up project structure at: {root_path}")
    ensure_directories(root_path)
    print("Project structure setup complete.")


if __name__ == "__main__":
    main()