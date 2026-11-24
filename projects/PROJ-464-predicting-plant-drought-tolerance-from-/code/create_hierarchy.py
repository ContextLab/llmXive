"""
Script to initialise the required project directory hierarchy for the
drought‑tolerance pipeline.

This task (T001a) must create the following top‑level directories
under the repository root:

    data/raw/
    data/derived/
    code/
    tests/
    docs/
    contracts/
    results/

The platform owns the ``state/`` directory, so this script deliberately
does **not** create it – it will be created by the platform when needed.
Creating ``state/`` here would shadow the platform‑owned path and is
prohibited by the project guidelines.

The script is idempotent: running it multiple times will not raise an
error and will leave the existing structure untouched.
"""

import sys
from pathlib import Path

def _project_root() -> Path:
    """
    Resolve the repository root (the directory that contains the top‑level
    folders ``code/``, ``data/`` etc.).  The script lives in ``code/``, so
    the root is its parent directory.
    """
    return Path(__file__).resolve().parent.parent

def _required_directories(root: Path) -> dict:
    """
    Mapping of logical directory names to their absolute ``Path`` objects.
    """
    return {
        "data_raw": root / "data" / "raw",
        "data_derived": root / "data" / "derived",
        "code": root / "code",
        "tests": root / "tests",
        "docs": root / "docs",
        "contracts": root / "contracts",
        "results": root / "results",
    }

def ensure_directories() -> None:
    """
    Create all required directories if they do not already exist.
    """
    root = _project_root()
    dirs = _required_directories(root)

    for name, path in dirs.items():
        try:
            path.mkdir(parents=True, exist_ok=True)
        except Exception as exc:  # pragma: no cover
            print(f"Failed to create {name} at {path}: {exc}", file=sys.stderr)
            raise

def get_config_summary() -> dict:
    """
    Return a dictionary summarising the created directory paths.
    """
    root = _project_root()
    dirs = _required_directories(root)
    return {
        "project_root": str(root),
        "directories": {name: str(p) for name, p in dirs.items()},
    }

def main() -> None:
    """
    Entry point: create the hierarchy and emit a short human‑readable
    summary.
    """
    ensure_directories()
    summary = get_config_summary()
    print("Project directory hierarchy created:")
    for name, path in summary["directories"].items():
        print(f"  {name}: {path}")

if __name__ == "__main__":
    # Exit with a non‑zero status if an unexpected exception occurs.
    try:
        main()
    except Exception as exc:  # pragma: no cover
        print(f"Error while creating hierarchy: {exc}", file=sys.stderr)
        sys.exit(1)