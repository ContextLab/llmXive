import os
import sys
from pathlib import Path


def create_structure() -> None:
    """Create the project directory structure."""
    dirs = [
        "code",
        "data",
        "data/raw",
        "data/processed",
        "data/results",
        "tests",
        "state",
        "state/projects",
        "contracts",
    ]
    for d in dirs:
        os.makedirs(d, exist_ok=True)
        print(f"Created directory: {d}")


def main() -> None:
    """Main entry point for project setup."""
    create_structure()
    print("Project structure created successfully.")


if __name__ == "__main__":
    main()
