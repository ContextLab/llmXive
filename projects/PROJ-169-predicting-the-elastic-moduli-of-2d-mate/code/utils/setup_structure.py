"""Utility to create the project directory structure."""
import os
from pathlib import Path

def main():
    """Create the standard project directories."""
    root = Path(__file__).resolve().parent.parent.parent
    dirs = [
        root / "code",
        root / "data" / "raw",
        root / "data" / "processed",
        root / "data" / "results",
        root / "tests" / "unit",
        root / "tests" / "integration",
        root / "docs",
        root / "state" / "projects",
    ]
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)
    print(f"Created project structure in {root}")

if __name__ == "__main__":
    main()
