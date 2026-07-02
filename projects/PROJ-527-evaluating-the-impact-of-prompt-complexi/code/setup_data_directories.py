"""
Script to setup the required data directory structure for the project.
Creates data/raw, data/processed, and data/results directories.
"""

import os
from pathlib import Path


def main() -> None:
    """Create the standard data directory structure."""
    # Define base directories relative to project root
    base_dirs = [
        "data/raw",
        "data/processed",
        "data/results",
    ]

    for dir_path in base_dirs:
        path = Path(dir_path)
        path.mkdir(parents=True, exist_ok=True)
        print(f"Created directory: {path}")

    # Verify structure
    print("\nDirectory structure verification:")
    for dir_path in base_dirs:
        path = Path(dir_path)
        if path.is_dir():
            print(f"  [OK] {path} exists")
        else:
            print(f"  [FAIL] {path} missing")


if __name__ == "__main__":
    main()