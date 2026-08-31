import os
import sys
from pathlib import Path

def create_project_structure():
    """Creates the project directory structure."""

    root_dir = Path(".")

    # Create directories
    for dir_path in [
        root_dir / "code",
        root_dir / "data",
        root_dir / "data/raw",
        root_dir / "data/processed",
        root_dir / "results",
        root_dir / "tests",
        root_dir / "tests/unit",
        root_dir / "tests/integration",
        root_dir / "specs"
    ]:
        dir_path.mkdir(parents=True, exist_ok=True)

def main():
    """Main function to create the project structure."""
    create_project_structure()
    print("Project structure created successfully.")

if __name__ == "__main__":
    main()
