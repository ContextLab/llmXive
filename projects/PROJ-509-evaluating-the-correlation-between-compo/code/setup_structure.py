import os
import sys
from pathlib import Path

def main():
    """Create project structure."""
    base = Path(__file__).parent.parent
    dirs = [
        "data/raw",
        "data/elemental_properties",
        "data/processed",
        "data/evaluation",
        "data/logs",
        "tests/contract",
        "tests/unit",
        "contracts"
    ]
    for d in dirs:
        (base / d).mkdir(parents=True, exist_ok=True)
    print("Project structure created.")

if __name__ == "__main__":
    main()
