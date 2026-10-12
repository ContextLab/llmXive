"""
create_project_tree.py

Script to create the canonical project directory tree required for the
Socratic Transformers pipeline.

Expected layout (relative to this script's directory, which is the project's
``code`` folder):

    src/
    data/
        raw/
        processed/
        results/
    tests/
    state/

The script is idempotent – existing directories are left untouched.
It exits with code 0 on success and raises any exception otherwise.
"""

import sys
from pathlib import Path

def create_directories(base_path: Path) -> None:
    """
    Create the required directory hierarchy under ``base_path``.

    Parameters
    ----------
    base_path: Path
        The ``code`` directory of the project.
    """
    # Define the relative directories required by the specification
    required_dirs = [
        base_path / "src",
        base_path / "data" / "raw",
        base_path / "data" / "processed",
        base_path / "data" / "results",
        base_path / "tests",
        base_path / "state",
    ]

    for d in required_dirs:
        d.mkdir(parents=True, exist_ok=True)

def main() -> int:
    """
    Entry point for the script.

    Returns
    -------
    int
        Exit status (0 = success, non‑zero = failure).
    """
    try:
        # The script resides in ``code``; its parent directory is the target root.
        code_dir = Path(__file__).resolve().parent
        create_directories(code_dir)
    except Exception as exc:
        # Log the exception to stderr and propagate a non‑zero exit code.
        print(f"Error while creating project directories: {exc}", file=sys.stderr)
        return 1
    return 0

if __name__ == "__main__":
    sys.exit(main())