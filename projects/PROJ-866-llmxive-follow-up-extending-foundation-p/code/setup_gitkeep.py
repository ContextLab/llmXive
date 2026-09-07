import os
import sys
from pathlib import Path


def create_gitkeep_in_directory(dir_path: str) -> None:
    """Create a .gitkeep file in a directory.

    Args:
        dir_path: Path to the directory.
    """
    gitkeep_path = os.path.join(dir_path, ".gitkeep")
    if not os.path.exists(gitkeep_path):
        with open(gitkeep_path, "w") as f:
            f.write("# Git keep file\n")
        print(f"Created .gitkeep in {dir_path}")


def initialize_data_directories() -> None:
    """Initialize data directories with .gitkeep files."""
    dirs = [
        "data",
        "data/raw",
        "data/processed",
        "data/results",
    ]
    for d in dirs:
        os.makedirs(d, exist_ok=True)
        create_gitkeep_in_directory(d)


def main() -> None:
    """Main entry point for gitkeep setup."""
    initialize_data_directories()
    print("Data directories initialized with .gitkeep files.")


if __name__ == "__main__":
    main()
