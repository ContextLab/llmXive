#!/usr/bin/env python3
"""
Script to ensure the core project directories exist:
- code/
- tests/
- state/

This script is idempotent and can be run multiple times without side effects.
"""
import sys
from pathlib import Path

def ensure_dir(path: Path) -> None:
    """Create a directory if it does not exist."""
    path.mkdir(parents=True, exist_ok=True)

def main() -> int:
    """Create required top‑level directories."""
    required_dirs = ["code", "tests", "state"]
    for dir_name in required_dirs:
        ensure_dir(Path(dir_name))
    print(f"Ensured existence of directories: {', '.join(required_dirs)}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
