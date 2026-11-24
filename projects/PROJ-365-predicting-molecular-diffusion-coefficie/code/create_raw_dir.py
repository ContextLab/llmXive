"""Create the raw‑data directory for the project.

This script ensures that ``data/raw`` exists. It is used as the
first step of the data‑acquisition phase and satisfies task T001.
"""

from pathlib import Path
from utils.config import get_project_root

def get_raw_dir() -> Path:
    """Return the absolute path to the ``data/raw`` directory."""
    return get_project_root() / "data" / "raw"

def ensure_raw_dir() -> Path:
    """Create ``data/raw`` if it does not exist and return the path."""
    raw_dir = get_raw_dir()
    raw_dir.mkdir(parents=True, exist_ok=True)
    return raw_dir

def main() -> None:
    """Entry point: create the directory and report success."""
    created_path = ensure_raw_dir()
    print(f"Raw data directory ensured at: {created_path}")

if __name__ == "__main__":
    main()
