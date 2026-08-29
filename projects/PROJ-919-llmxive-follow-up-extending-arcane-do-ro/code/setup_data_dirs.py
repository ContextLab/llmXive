import os
from pathlib import Path
import sys

def setup_directories():
    """Creates the necessary data directories if they don't exist."""
    for dir_path in [
        "data/raw/",
        "data/derived/",
        "data/gold_standard/",
        "artifacts/",
    ]:
        Path(dir_path).mkdir(parents=True, exist_ok=True)

if __name__ == "__main__":
    setup_directories()