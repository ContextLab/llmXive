import os
import sys
from pathlib import Path

def create_data_directories():
    """
    Creates the data and results directories required for the project.
    Ensures data/raw, data/processed, data/metadata, and results exist.
    """
    root = Path(__file__).parent
    dirs = [
        root / "data" / "raw",
        root / "data" / "processed",
        root / "data" / "metadata",
        root / "results",
    ]

    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)
    
    return [str(d) for d in dirs]

if __name__ == "__main__":
    created = create_data_directories()
    print(f"Created data directories: {created}")
