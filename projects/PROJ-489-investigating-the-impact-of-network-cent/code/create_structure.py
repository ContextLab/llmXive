"""Utility script to create required project directory structure.

Running this script will ensure the following directories exist relative to the
project root:

- code/
- data/raw/
- data/processed/
- data/metrics/
- data/results/
- tests/unit/
- tests/integration/
"""

import sys
from pathlib import Path

def create_directories(base_path: Path) -> None:
    """
    Create the required directory hierarchy under ``base_path``.
    Existing directories are left untouched.
    """
    dirs = [
        base_path / "code",
        base_path / "data" / "raw",
        base_path / "data" / "processed",
        base_path / "data" / "metrics",
        base_path / "data" / "results",
        base_path / "tests" / "unit",
        base_path / "tests" / "integration",
    ]
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)

def verify_directories(base_path: Path) -> None:
    """
    Verify that all required directories exist.
    Raises:
        RuntimeError: If any required directory is missing.
    """
    missing = []
    dirs = [
        base_path / "code",
        base_path / "data" / "raw",
        base_path / "data" / "processed",
        base_path / "data" / "metrics",
        base_path / "data" / "results",
        base_path / "tests" / "unit",
        base_path / "tests" / "integration",
    ]
    for d in dirs:
        if not d.is_dir():
            missing.append(str(d))
    if missing:
        raise RuntimeError(
            f"The following required directories are missing: {', '.join(missing)}"
        )

def main() -> int:
    """
    Entry point for the script.
    Returns:
        int: Exit code (0 on success, non‑zero on failure).
    """
    # The repository root is two levels up from this file:
    #   code/create_structure.py -> repository root
    project_root = Path(__file__).resolve().parents[1]

    create_directories(project_root)

    try:
        verify_directories(project_root)
    except RuntimeError as e:
        print(e, file=sys.stderr)
        return 1

    print("All required directories are present.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
