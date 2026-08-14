import os
import sys
from pathlib import Path

from config import load_paths


def main() -> None:
    """Main entry point for setup."""
    paths = load_paths()
    dirs = [
        paths["data_raw"],
        paths["data_processed"],
        paths["data_evaluation"],
        paths["data_logs"],
        paths["data_elemental"],
    ]
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)
    print("Directory structure created")


if __name__ == "__main__":
    main()
