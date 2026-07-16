"""
Helper script to ensure data directories exist.
"""
import os
from pathlib import Path

def setup_data_directories():
    """Creates data/raw, data/processed, data/derived if they don't exist."""
    # Assuming this is run from code/
    root = Path(__file__).resolve().parent.parent
    data_dirs = ["data/raw", "data/processed", "data/derived"]
    for d in data_dirs:
        path = root / d
        path.mkdir(parents=True, exist_ok=True)
        print(f"Ensured directory exists: {path}")

if __name__ == "__main__":
    setup_data_directories()