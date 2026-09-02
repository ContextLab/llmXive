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
    base_dir = Path(".")
    
    # Define required directories
    directories = [
        "code",
        "data/raw",
        "data/processed",
        "data/interim",
        "data/results",
        "tests/unit",
        "tests/contract",
        "tests/integration",
        "specs/001-statistical-cognitive-decline/contracts"
    ]
    
    print("Creating project directory structure...")
    for dir_path in directories:
        full_path = base_dir / dir_path
        create_directory(str(full_path))
    
    print("Project structure setup complete.")

if __name__ == "__main__":
    main()