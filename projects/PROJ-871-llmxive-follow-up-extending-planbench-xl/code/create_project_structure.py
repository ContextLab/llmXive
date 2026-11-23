"""
create_project_structure.py

This script creates the required project scaffold for the
``PROJ-871-llmxive-follow-up-extending-planbench-xl`` project and
verifies that the three top‑level directories ``code/``, ``data/`` and
``tests/`` exist.

It is intended to be the verification step for task **T001**.
"""

import os
from pathlib import Path
import sys

def ensure_dir(path: Path) -> None:
    """Create *path* if it does not exist."""
    try:
        path.mkdir(parents=True, exist_ok=True)
    except Exception as exc:
        raise RuntimeError(f"Failed to create directory {path!s}: {exc}") from exc

def verify_structure(root: Path) -> None:
    """Assert that the required sub‑directories exist under *root*."""
    required = ["code", "data", "tests"]
    missing = [d for d in required if not (root / d).is_dir()]
    if missing:
        raise AssertionError(f"Missing required directories under {root!s}: {missing}")
    # If we reach here, everything is present.
    print(f"Verification successful: all required directories exist under {root!s}")

def main() -> int:
    """
    Entry point.

    The script works regardless of the current working directory.
    It resolves the project root as the parent of the directory that
    contains this file (i.e. ``.../code`` → project root).
    """
    # Resolve the project root (two levels up from this file)
    script_path = Path(__file__).resolve()
    project_root = script_path.parent.parent

    # Create the required directories (idempotent)
    for sub in ("code", "data", "tests"):
        ensure_dir(project_root / sub)

    # Verify the structure
    try:
        verify_structure(project_root)
    except AssertionError as err:
        print(f"ERROR: {err}", file=sys.stderr)
        return 1
    except Exception as exc:
        print(f"Unexpected error: {exc}", file=sys.stderr)
        return 1

    return 0

if __name__ == "__main__":
    sys.exit(main())