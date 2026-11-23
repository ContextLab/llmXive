"""
Script to ensure the required data directory structure exists.

Creates:
  - data/raw/
  - data/processed/

The script is idempotent: running it multiple times will not raise errors.
"""

import sys
from pathlib import Path

def create_directory(dir_path: Path) -> None:
    """Create a directory if it does not exist.

    Args:
        dir_path (Path): The directory to create.
    """
    try:
        dir_path.mkdir(parents=True, exist_ok=True)
        print(f"Created directory: {dir_path}")
    except Exception as e:
        print(f"Failed to create directory {dir_path}: {e}", file=sys.stderr)
        raise

def main() -> None:
    """Main entry point: create the required data directories."""
    project_root = Path(__file__).resolve().parents[1]  # project root (one level above code/)
    raw_dir = project_root / "data" / "raw"
    processed_dir = project_root / "data" / "processed"

    create_directory(raw_dir)
    create_directory(processed_dir)

if __name__ == "__main__":
    main()