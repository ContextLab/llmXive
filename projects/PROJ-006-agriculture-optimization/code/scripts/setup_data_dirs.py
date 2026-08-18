"""
Script to set up the required data directory structure for the project.
Creates data/raw/, data/processed/, and data/logs/ directories.
"""
import os
import sys
from pathlib import Path

def ensure_dir(path: Path) -> None:
    """Ensure a directory exists, creating it if necessary."""
    if not path.exists():
        path.mkdir(parents=True, exist_ok=True)
        print(f"Created directory: {path}")
    else:
        print(f"Directory already exists: {path}")

def main() -> int:
    """Main entry point to set up data directories."""
    # Determine project root (assumes this script is in code/scripts/)
    script_dir = Path(__file__).resolve().parent
    project_root = script_dir.parent.parent

    data_root = project_root / "data"

    # Define required directories
    required_dirs = [
        data_root / "raw",
        data_root / "processed",
        data_root / "logs",
    ]

    print(f"Setting up data directories under: {data_root}")

    for dir_path in required_dirs:
        ensure_dir(dir_path)

    print("Data directory setup complete.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
