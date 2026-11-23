"""
Script to ensure directory structure exists (T001a verification).
This script is run once to initialize the project tree.
"""
import os
import sys
from pathlib import Path

def main():
    root = Path(__file__).parent
    dirs = [
        "data/raw",
        "data/processed",
        "code/models",
        "code/metrics",
        "code/stats",
        "results",
        "tests/unit",
        "tests/integration",
        "code/utils",
        "figures"
    ]

    created = []
    for d in dirs:
        path = root / d
        if not path.exists():
            path.mkdir(parents=True, exist_ok=True)
            created.append(str(path))
            print(f"Created directory: {path}")
        else:
            print(f"Directory exists: {path}")

    if not created:
        print("All directories already exist.")
    else:
        print(f"\nTotal directories created: {len(created)}")

if __name__ == "__main__":
    main()