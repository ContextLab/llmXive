"""
Script to set up the required directory structure for the project.
Creates data/raw/, data/processed/, and data/logs/ directories.
"""
import os
import sys
from pathlib import Path


def ensure_dir(path: Path) -> None:
    """Create a directory if it does not exist."""
    if not path.exists():
        path.mkdir(parents=True, exist_ok=True)
        print(f"Created directory: {path}")
    else:
        print(f"Directory already exists: {path}")


def main() -> int:
    """Main entry point for setting up data directories."""
    # Determine project root (assuming this script is in code/scripts/)
    script_path = Path(__file__).resolve()
    project_root = script_path.parent.parent

    # Define data directories relative to project root
    data_dirs = [
        project_root / "data" / "raw",
        project_root / "data" / "processed",
        project_root / "data" / "logs",
    ]

    print(f"Setting up data directories under: {project_root}")

    for dir_path in data_dirs:
        ensure_dir(dir_path)

    print("Data directory structure setup complete.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
