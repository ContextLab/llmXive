"""Create project root directory structure for PROJ-405.

This script creates the following directories relative to the repository root:
- projects/PROJ-405/
  - code/
  - data/
  - tests/
  - artifacts/

It is safe to run multiple times; existing directories will be left unchanged.
"""

import sys
from pathlib import Path

def main() -> None:
    base_dir = Path("projects") / "PROJ-405"
    subdirs = ["code", "data", "tests", "artifacts"]
    for sub in subdirs:
        dir_path = base_dir / sub
        try:
            dir_path.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {dir_path}")
        except Exception as exc:
            print(f"Failed to create {dir_path}: {exc}", file=sys.stderr)
            sys.exit(1)
    print("Project directory structure created successfully.")

if __name__ == "__main__":
    main()