#!/usr/bin/env python
"""
create_structure.py
-------------------
Utility script to create the required project directory structure for the
llmXive follow‑up project.

Directories created (relative to the project root):
  code/
  data/
    raw/
    processed/
    results/
  models/
  tests/
    unit/
    integration/
    contract/
  state/

The script is idempotent – existing directories are left untouched.
It prints a short summary of actions performed.
"""
import sys
from pathlib import Path

def get_project_root() -> Path:
    """
    Return the absolute path to the project root directory.
    The script resides in <project_root>/code/, so the root is its parent.
    """
    return Path(__file__).resolve().parent.parent

def create_directories(root: Path) -> None:
    """
    Create all required directories under the given root.

    Parameters
    ----------
    root : Path
        The project root directory.
    """
    # Define the directory tree relative to the project root
    dirs = [
        root / "code",
        root / "data" / "raw",
        root / "data" / "processed",
        root / "data" / "results",
        root / "models",
        root / "tests" / "unit",
        root / "tests" / "integration",
        root / "tests" / "contract",
        root / "state",
    ]

    for d in dirs:
        if not d.exists():
            d.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {d}")
        else:
            print(f"Directory already exists: {d}")

def main(argv=None) -> int:
    """
    Entry point for the script.

    Returns
    -------
    int
        Exit code (0 for success, non‑zero for failure).
    """
    if argv is None:
        argv = sys.argv[1:]

    # No command‑line arguments are required for this utility.
    # The presence of any arguments is ignored to keep the interface simple.
    root = get_project_root()
    try:
        create_directories(root)
    except Exception as e:
        print(f"Error while creating directories: {e}", file=sys.stderr)
        return 1

    return 0

if __name__ == "__main__":
    sys.exit(main())
