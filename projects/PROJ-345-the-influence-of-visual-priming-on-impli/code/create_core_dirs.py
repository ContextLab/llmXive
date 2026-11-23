"""
Core Directory Creation Script
Creates the essential data directories required for the pipeline:
- data/raw
- data/processed
- data/primes
- data/targets
The script is idempotent and can be run multiple times without error.
"""
import sys
from pathlib import Path

def create_directories():
    """
    Create the core data directories if they do not already exist.
    """
    base_dirs = [
        Path("data") / "raw",
        Path("data") / "processed",
        Path("data") / "primes",
        Path("data") / "targets",
    ]
    for d in base_dirs:
        d.mkdir(parents=True, exist_ok=True)
        print(f"Ensured directory exists: {d}")

def main():
    """
    Entry point for the script when executed from the command line.
    """
    try:
        create_directories()
    except Exception as e:
        print(f"Error creating directories: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
