import os
import sys
from pathlib import Path

def create_directory(path: Path) -> None:
    """Create a directory if it does not exist."""
    if not path.exists():
        path.mkdir(parents=True, exist_ok=True)
        print(f"Created directory: {path}")
    else:
        print(f"Directory already exists: {path}")

def main() -> None:
    """Create the required data directories."""
    # Define the base data directory relative to the project root
    # Assuming the script is run from the project root or code/ directory
    # We use a relative path strategy that works from the code/ directory
    project_root = Path(__file__).resolve().parent.parent
    data_base = project_root / "data"

    directories = [
        data_base / "raw",
        data_base / "processed",
        data_base / "synthetic",
        data_base / "derivation_logs",
    ]

    for directory in directories:
        create_directory(directory)

    print("Data directory structure created successfully.")

if __name__ == "__main__":
    main()