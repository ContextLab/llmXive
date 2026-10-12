#!/usr/bin/env python3
"""
Script to create the canonical project directory layout required for the
pipeline. It creates the following directories (relative to the project root):

  - code/
  - tests/
  - data/raw/
  - data/processed/
  - specs/001‑exploring‑the‑correlation‑between‑molecu/contracts/
  - state/pending/

After creation it asserts that each directory exists. The script exits with
status 0 on success; any assertion failure will raise an AssertionError.
"""

import os
from pathlib import Path
import sys

def main() -> None:
    # Determine the project root (parent of the 'scripts' directory)
    script_path = Path(__file__).resolve()
    project_root = script_path.parent.parent

    # Define the required directories
    required_dirs = [
        project_root / "code",
        project_root / "tests",
        project_root / "data" / "raw",
        project_root / "data" / "processed",
        project_root / "specs" / "001‑exploring‑the‑correlation‑between‑molecu" / "contracts",
        project_root / "state" / "pending",
    ]

    # Create each directory (including any missing parents)
    for d in required_dirs:
        d.mkdir(parents=True, exist_ok=True)

    # Verify that all directories now exist
    for d in required_dirs:
        assert d.is_dir(), f"Directory {d} was not created"

    print("All required directories have been created successfully.", flush=True)

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"Error during setup: {e}", file=sys.stderr, flush=True)
        sys.exit(1)