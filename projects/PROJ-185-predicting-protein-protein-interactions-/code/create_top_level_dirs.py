"""Create the required top‑level project directories.

This script ensures that the following directories exist at the project
root:

  - src
  - tests
  - data
  - results
  - docs
  - contracts

It is used by the T001 task to satisfy the `test_skeleton.py` unit test.
The directories are created if they do not already exist; existing
contents are left untouched to avoid deleting source code or other
artifacts.
"""

import sys
from pathlib import Path

def create_top_level_dirs() -> None:
    """Create the six required top‑level directories if they are missing."""
    required = ["src", "tests", "data", "results", "docs", "contracts"]
    for name in required:
        Path(name).mkdir(parents=True, exist_ok=True)

if __name__ == "__main__":
    try:
        create_top_level_dirs()
    except Exception as exc:
        print(f"Error creating directories: {exc}", file=sys.stderr)
        sys.exit(1)
    else:
        print("Top‑level directories ensured to exist.")
