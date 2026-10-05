"""
Module to create the data/raw directory for source CSVs.
This is the implementation for Task T000a.
"""
from pathlib import Path
from utils.config import get_project_root

def get_raw_dir() -> Path:
    """
    Returns the path to the data/raw directory.
    """
    root = get_project_root()
    return root / "data" / "raw"

def ensure_raw_dir() -> Path:
    """
    Ensures the data/raw directory exists. Creates it if it does not.
    Returns the path to the directory.
    """
    raw_dir = get_raw_dir()
    raw_dir.mkdir(parents=True, exist_ok=True)
    return raw_dir

def main() -> None:
    """
    Main entry point to create the raw directory.
    """
    try:
        path = ensure_raw_dir()
        print(f"Successfully ensured directory exists: {path}")
    except Exception as e:
        print(f"Failed to create raw directory: {e}")
        raise

if __name__ == "__main__":
    main()