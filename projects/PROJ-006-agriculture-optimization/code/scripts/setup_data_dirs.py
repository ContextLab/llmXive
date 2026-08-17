import os
import sys
from pathlib import Path

def ensure_dir(path: Path) -> None:
    """Create directory if it does not exist."""
    if not path.exists():
        path.mkdir(parents=True, exist_ok=True)
    elif not path.is_dir():
        raise RuntimeError(f"Path exists but is not a directory: {path}")

def main() -> None:
    """
    Setup the data directory structure for PROJ-006-agriculture-optimization.
    Creates:
      - data/raw/
      - data/processed/
      - data/logs/
    """
    # Determine project root (assumed to be the parent of 'scripts')
    current_file = Path(__file__).resolve()
    project_root = current_file.parent.parent

    data_root = project_root / "data"
    raw_dir = data_root / "raw"
    processed_dir = data_root / "processed"
    logs_dir = data_root / "logs"

    dirs_to_create = [raw_dir, processed_dir, logs_dir]

    for dir_path in dirs_to_create:
        ensure_dir(dir_path)
        print(f"Created directory: {dir_path}")

    # Verify creation
    all_created = all(d.exists() and d.is_dir() for d in dirs_to_create)
    if not all_created:
        raise RuntimeError("Failed to create one or more data directories.")

    print("Data directory structure setup complete.")

if __name__ == "__main__":
    main()
