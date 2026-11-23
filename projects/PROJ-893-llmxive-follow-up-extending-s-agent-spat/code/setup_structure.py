import os
import sys
from pathlib import Path

def create_directories(base_path: Path) -> None:
    """
    Create the project directory structure as defined in plan.md.
    
    Directories created:
    - code/
    - data/raw/
    - data/derived/
    - data/results/
    - specs/
    - tests/
    """
    directories = [
        "code",
        "data/raw",
        "data/derived",
        "data/results",
        "specs",
        "tests",
        "state/projects"
    ]
    
    for dir_path in directories:
        full_path = base_path / dir_path
        full_path.mkdir(parents=True, exist_ok=True)
        print(f"Created directory: {full_path}")

def main() -> None:
    """Entry point for directory structure creation."""
    base_path = Path.cwd()
    print(f"Creating project structure in: {base_path}")
    create_directories(base_path)
    print("Project structure creation complete.")

if __name__ == "__main__":
    main()
