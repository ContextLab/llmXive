import os
import sys
from pathlib import Path

def create_directory(path: Path) -> None:
    """Create a directory if it does not exist."""
    path.mkdir(parents=True, exist_ok=True)
    # Ensure the directory is not empty by creating a .gitkeep file
    gitkeep = path / ".gitkeep"
    if not gitkeep.exists():
        gitkeep.write_text("# Directory placeholder\n")

def main() -> None:
    """Create the required data directories for the project."""
    project_root = Path("projects/PROJ-560-embodied-curriculum-learning-physical-si")
    data_root = project_root / "data"

    directories = [
        data_root / "raw",
        data_root / "processed",
        data_root / "synthetic",
        data_root / "derivation_logs",
    ]

    for directory in directories:
        create_directory(directory)
        print(f"Created directory: {directory}")

if __name__ == "__main__":
    main()