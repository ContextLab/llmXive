"""Utility to create the basic directory layout for the project."""
import os
import sys
from pathlib import Path

def main() -> None:
    root = Path.cwd()
    subdirs = [
        "code",
        "data/raw",
        "data/processed",
        "results",
        "tests",
        "docs",
    ]
    for sub in subdirs:
        (root / sub).mkdir(parents=True, exist_ok=True)
    print("Project structure created.")

if __name__ == "__main__":
    main()