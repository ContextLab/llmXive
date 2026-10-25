"""Create the core directory layout for the project.

This script ensures that the essential top‑level directories exist:
- code/
- data/raw/
- data/processed/
- models/
- results/
- tests/
- contracts/

It can be safely re‑run; existing directories are left untouched.
"""

from pathlib import Path
import sys

def main() -> None:
    """Create required directories."""
    # List of directories relative to the project root
    dirs = [
        Path("code"),
        Path("data", "raw"),
        Path("data", "processed"),
        Path("models"),
        Path("results"),
        Path("tests"),
        Path("contracts"),
    ]

    for d in dirs:
        try:
            d.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            print(f"Failed to create directory {d}: {e}", file=sys.stderr)
            sys.exit(1)

    print("Core directory layout created successfully.")


if __name__ == "__main__":
    main()