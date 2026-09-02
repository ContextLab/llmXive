import os
import sys
from pathlib import Path

from config import get_project_root, ensure_directories_exist


def create_directories() -> None:
    """
    Create the required directory structure for the project.

    This function ensures the existence of the following directories relative
    to the project root:
    - code/
    - tests/
    - data/raw
    - data/derivatives
    - data/processed
    - state/

    It uses the existing `ensure_directories_exist` helper from `code/config.py`.
    """
    root = get_project_root()
    directories = [
        "code",
        "tests",
        "data/raw",
        "data/derivatives",
        "data/processed",
        "state",
    ]

    print(f"Creating directory structure under: {root}")
    for dir_name in directories:
        ensure_directories_exist(dir_name)
        print(f"  - Created/Verified: {dir_name}")

    print("Directory structure setup complete.")


if __name__ == "__main__":
    create_directories()
