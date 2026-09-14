import os
import sys
from pathlib import Path

def main():
    """
    Creates the project structure as defined in the tasks.md file.
    """
    project_root = Path(".")

    # Define directories to create
    directories = [
        project_root / "src/data",
        project_root / "src/models",
        project_root / "src/training",
        project_root / "src/analysis",
        project_root / "src/config",
        project_root / "tests/unit",
        project_root / "tests/integration",
        project_root / "contracts",
        project_root / "data/raw",
        project_root / "data/processed",
        project_root / "data/results",
        project_root / "artifacts",
    ]

    # Create directories if they don't exist
    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)
        print(f"Created directory: {directory}")

    print("Project structure created successfully.")

if __name__ == "__main__":
    main()
