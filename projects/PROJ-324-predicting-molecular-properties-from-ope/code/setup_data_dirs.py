import os
from pathlib import Path
import logging

def main() -> None:
    """
    Main entry point for setting up data directories.
    """
    dirs = [
        "code",
        "tests",
        "data/raw",
        "data/processed",
        "data/derived",
        "figures"
    ]
    for d in dirs:
        Path(d).mkdir(parents=True, exist_ok=True)
        logging.info(f"Created directory: {d}")

if __name__ == "__main__":
    main()
