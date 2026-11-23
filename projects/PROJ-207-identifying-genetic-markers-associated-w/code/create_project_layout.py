#!/usr/bin/env python3
"""
Task T001 – Create the standard project directory layout.

This script creates the required top‑level directories:
    code/
    data/raw/
    data/interim/
    data/processed/
    docs/
    tests/

It is idempotent – existing directories are left untouched.
"""
import sys
from pathlib import Path

def main() -> None:
    # Define the directories to create relative to the repository root.
    dirs = [
        Path("code"),
        Path("data/raw"),
        Path("data/interim"),
        Path("data/processed"),
        Path("docs"),
        Path("tests"),
    ]

    for d in dirs:
        try:
            d.mkdir(parents=True, exist_ok=True)
        except Exception as exc:
            print(f"Failed to create directory {d}: {exc}", file=sys.stderr)
            sys.exit(1)

    print("Project directory layout created successfully.")

if __name__ == "__main__":
    main()
