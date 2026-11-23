"""
Project directory setup module.
Creates the required directory structure for the perovskite stability project.
"""
import os
from pathlib import Path


def create_directories() -> None:
    """
    Create the standard project directory structure.
    
    Creates the following directories relative to the project root:
    - code/
    - data/raw/
    - data/processed/
    - tests/
    - docs/
    - state/
    """
    project_root = Path(__file__).resolve().parent.parent
    
    required_dirs = [
        "code",
        "data/raw",
        "data/processed",
        "tests",
        "docs",
        "state"
    ]
    
    for dir_path in required_dirs:
        full_path = project_root / dir_path
        full_path.mkdir(parents=True, exist_ok=True)
        print(f"Created directory: {full_path}")


if __name__ == "__main__":
    create_directories()