"""
Script to create the required project directory layout.

This script is intended to be run as part of task T001. It creates the
following directories at the repository root (relative to the project
root):
  - data/raw/
  - data/processed/
  - results/
  - logs/
  - code/
  - tests/

The script is idempotent: running it multiple times will not raise an
error and will leave the existing structure intact.
"""

import os
from pathlib import Path
import sys

def main() -> int:
    # Define the required directories relative to the project root
    required_dirs = [
        Path("data") / "raw",
        Path("data") / "processed",
        Path("results"),
        Path("logs"),
        Path("code"),
        Path("tests"),
    ]

    for d in required_dirs:
        try:
            d.mkdir(parents=True, exist_ok=True)
            # Ensure the directory was created
            if not d.is_dir():
                print(f"Failed to create directory: {d}", file=sys.stderr)
                return 1
        except Exception as e:
            print(f"Error creating directory {d}: {e}", file=sys.stderr)
            return 1

    print("Project directory layout created successfully.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
