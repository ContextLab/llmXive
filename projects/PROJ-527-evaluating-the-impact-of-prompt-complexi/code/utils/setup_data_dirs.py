"""
Script to create the required data directory structure.
Creates data/raw, data/processed, and data/results directories.
"""
import os
from pathlib import Path

def main():
    """Create the standard data directory structure."""
    base_dir = Path(__file__).resolve().parent.parent.parent
    data_dir = base_dir / "data"

    dirs = [
        data_dir / "raw",
        data_dir / "processed",
        data_dir / "results",
    ]

    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)
        print(f"Created: {d}")

    # Verify existence
    all_exist = all(d.exists() and d.is_dir() for d in dirs)
    if all_exist:
        print("All data directories successfully created.")
    else:
        raise RuntimeError("Failed to create one or more data directories.")

if __name__ == "__main__":
    main()
