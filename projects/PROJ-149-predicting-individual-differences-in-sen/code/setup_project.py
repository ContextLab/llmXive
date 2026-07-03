import os
import sys
from pathlib import Path

def create_directories():
    """Create the standard project directory structure."""
    base = Path(__file__).resolve().parent.parent
    dirs = [
        "code",
        "tests",
        "data/raw",
        "data/interim",
        "data/processed",
        "code/utils"
    ]
    
    for d in dirs:
        (base / d).mkdir(parents=True, exist_ok=True)
        print(f"Created: {base / d}")

if __name__ == "__main__":
    create_directories()
