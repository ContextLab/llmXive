"""Create the required top‑level project directories.

This script ensures that the following directories exist at the project
root and are empty (any existing files inside them are removed):

  - src
  - tests
  - data
  - results
  - docs
  - contracts

It is used by the T001 task to satisfy the `test_skeleton.py` unit test.
"""

import sys
from pathlib import Path
import shutil

def _ensure_empty_dir(dir_path: Path) -> None:
    """Create *dir_path* if it does not exist and remove any contents."""
    if dir_path.exists():
        # Remove all files and sub‑directories to guarantee emptiness.
        for child in dir_path.iterdir():
            if child.is_dir():
                shutil.rmtree(child)
            else:
                child.unlink()
    else:
        dir_path.mkdir(parents=True, exist_ok=True)

def create_top_level_dirs() -> None:
    """Create the six required top‑level directories as empty folders."""
    required = ["src", "tests", "data", "results", "docs", "contracts"]
    for name in required:
        _ensure_empty_dir(Path(name))

if __name__ == "__main__":
    try:
        create_top_level_dirs()
    except Exception as exc:
        # Propagate the error and exit with a non‑zero status so CI can see the failure.
        print(f"Error creating directories: {exc}", file=sys.stderr)
        sys.exit(1)
    else:
        print("Top‑level directories created successfully.")