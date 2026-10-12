#!/usr/bin/env python3
"""
T001 – Create project structure

This script creates the top‑level directories required for the project:
- code/
- data/
- tests/
- docs/
- artifacts/

It deliberately does **not** create a ``state/`` directory because that
location is owned by the platform and is managed automatically during
verification. Creating a local ``state/`` would shadow the platform's
state directory and cause verification failures.

The script is idempotent; existing directories are left untouched.
It exits with status 0 on success or propagates any unexpected exception.
"""

import sys
from pathlib import Path

# Use the shared logger from llmxive_toolkit for consistency
from llmxive_toolkit import get_logger

log = get_logger(__name__)

def create_directories(base_path: Path, dir_names):
    """
    Create each directory in ``dir_names`` under ``base_path``.
    ``exist_ok=True`` ensures the operation is idempotent.
    """
    for name in dir_names:
        dir_path = base_path / name
        try:
            dir_path.mkdir(parents=True, exist_ok=True)
            log.info("Created directory: %s", dir_path)
        except Exception as exc:
            log.error("Failed to create %s: %s", dir_path, exc)
            raise

def main():
    """
    Entry point for the script. It resolves the project root (the directory
    containing this script's parent) and creates the required folders.
    """
    # The script lives in <project_root>/code/, so the root is its parent.
    project_root = Path(__file__).resolve().parent.parent
    # NOTE: ``state`` is omitted intentionally – it is a platform‑owned path.
    required_dirs = ["code", "data", "tests", "docs", "artifacts"]
    create_directories(project_root, required_dirs)

    # Inform the user that the structure is ready.
    print("Project structure created successfully.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
