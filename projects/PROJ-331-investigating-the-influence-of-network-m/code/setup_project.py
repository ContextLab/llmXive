import os
import sys
from pathlib import Path

def create_directories():
    """Create the project directory structure."""
    base = Path(__file__).parent.parent
    dirs = [
        "code", "tests", "data/raw", "data/processed", "data/logs",
        "results", "state"
    ]
    for d in dirs:
        (base / d).mkdir(parents=True, exist_ok=True)
    print("Project directories created.")

if __name__ == "__main__":
    create_directories()