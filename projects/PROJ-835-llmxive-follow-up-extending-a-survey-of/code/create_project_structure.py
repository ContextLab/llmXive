#!/usr/bin/env python3
"""
create_project_structure.py

Creates the core project directories required by the implementation plan.
Directories created:
  - src/
  - tests/
  - data/
  - models/
  - results/

The `state/` directory is managed by the platform and is NOT created here.
"""
import sys
from pathlib import Path

def main() -> int:
    # Determine the project root (parent of the `code` directory)
    project_root = Path(__file__).resolve().parent.parent

    # List of directories to create (excluding platform‑owned `state/`)
    dirs_to_create = ["src", "tests", "data", "models", "results"]

    for rel_dir in dirs_to_create:
        dir_path = project_root / rel_dir
        try:
            dir_path.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {dir_path}")
        except Exception as e:
            print(f"Failed to create {dir_path}: {e}", file=sys.stderr)
            return 1

    return 0

if __name__ == "__main__":
    sys.exit(main())
