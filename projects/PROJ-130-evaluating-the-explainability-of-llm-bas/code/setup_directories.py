import os
import sys
from pathlib import Path

def ensure_directory(path_str: str) -> None:
    """
    Create a directory if it does not exist.
    Handles nested paths and ensures parent directories are created.
    """
    path = Path(path_str)
    if not path.exists():
        path.mkdir(parents=True, exist_ok=True)
        print(f"Created directory: {path}")
    else:
        print(f"Directory already exists: {path}")

def main() -> None:
    """
    Main entry point to create all required project directories.
    Creates:
      - explanations/
      - state/
      - tests/
    """
    # Define directories to create relative to project root
    directories = [
        "explanations",
        "state",
        "tests",
        # Ensure subdirectories for tests are also ready
        "tests/contract",
        "tests/integration",
    ]

    for dir_path in directories:
        ensure_directory(dir_path)

    print("\nDirectory setup complete.")

if __name__ == "__main__":
    main()
