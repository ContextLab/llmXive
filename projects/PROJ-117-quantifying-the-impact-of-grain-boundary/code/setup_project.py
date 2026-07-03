import os
import sys
from pathlib import Path

def create_directory(path: str) -> None:
    """Create a directory if it does not exist."""
    dir_path = Path(path)
    if not dir_path.exists():
        dir_path.mkdir(parents=True, exist_ok=True)
        print(f"Created directory: {dir_path}")
    else:
        print(f"Directory already exists: {dir_path}")

def main() -> None:
    """Create the project directory structure."""
    # Define the required directories relative to the project root
    directories = [
        "code",
        "data/raw",
        "data/processed",
        "models",
        "artifacts/reports",
        "artifacts/figures",
        "tests/unit",
        "tests/integration",
        "specs",
        "docs",
    ]

    for dir_path in directories:
        create_directory(dir_path)

    print("Project structure setup complete.")

if __name__ == "__main__":
    main()
