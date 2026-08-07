"""
Script to create the required directory structure for the project.
Ensures `code/` and `tests/` directories exist.
"""
import os
from pathlib import Path

def main():
    root = Path(__file__).parent.parent
    dirs = [
        root / "code",
        root / "tests",
        root / "data" / "raw",
        root / "data" / "derived",
        root / "figures",
        root / "logs",
    ]
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)
        print(f"Created/Verified: {d}")

if __name__ == "__main__":
    main()