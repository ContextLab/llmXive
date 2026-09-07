import os
import sys
from pathlib import Path


def create_data_directories() -> None:
    """Create the standard data directory structure."""
    dirs = [
        "data",
        "data/raw",
        "data/processed",
        "data/results",
    ]
    for d in dirs:
        os.makedirs(d, exist_ok=True)
        print(f"Created directory: {d}")


def main() -> None:
    """Main entry point for data directory setup."""
    create_data_directories()
    print("Data directories created successfully.")


if __name__ == "__main__":
    main()
