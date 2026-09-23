"""
Utility script to create the required project directory structure.

Directories created:
  - code/
  - data/raw/
  - data/processed/
  - tests/unit/
  - tests/integration/

The script can be run directly (`python code/create_directories.py`) or the
`create_directories` function can be imported and called from other code
(e.g., unit tests) with an optional `base_path` argument.
"""

import sys
from pathlib import Path
from typing import Optional

def create_directories(base_path: Optional[Path] = None) -> None:
    """
    Create the required directory hierarchy.

    Parameters
    ----------
    base_path : pathlib.Path | None
        Root directory under which the hierarchy will be created.
        If ``None`` (default), the project root is inferred from the
        location of this file (two levels up, i.e. the repository root).
    """
    if base_path is None:
        # This file lives in <repo_root>/code/, so two parents up is the repo root.
        base_path = Path(__file__).resolve().parents[1]

    # Define the required directories relative to the base path.
    dirs = [
        base_path / "code",
        base_path / "data" / "raw",
        base_path / "data" / "processed",
        base_path / "tests" / "unit",
        base_path / "tests" / "integration",
    ]

    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)

    # Simple feedback for interactive runs.
    print("Created/verified directories:")
    for d in dirs:
        print(f" - {d}")

def _main() -> int:
    """Entry‑point used when the module is executed as a script."""
    try:
        create_directories()
    except Exception as exc:  # pragma: no cover – defensive
        print(f"Error while creating directories: {exc}", file=sys.stderr)
        return 1
    return 0

if __name__ == "__main__":
    sys.exit(_main())