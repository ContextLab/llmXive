import os
from pathlib import Path

def setup_data_directories():
    """
    Create the required data directory structure for the project at the root.
    Ensures that data/ is not nested inside code/ and resides at the project root.
    """
    dirs = [
        "code",
        "data/raw",
        "data/processed",
        "data/results",
        "data/neural/processed",
        "data/text",
        "tests",
        "state",
        "logs",
    ]
    for d in dirs:
        path = Path(d)
        path.mkdir(parents=True, exist_ok=True)
        print(f"Created/Verified directory: {path}")

if __name__ == "__main__":
    setup_data_directories()