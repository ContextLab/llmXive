"""
Script to initialise the project directory hierarchy.

It simply calls ``ensure_directories`` from ``code.config`` and prints a
short summary of the created paths.  Running this script is the primary
verification step for task **T001a** – after execution the expected
folders must exist, allowing a ``tree`` command (or the unit test below)
to confirm the layout.
"""

import sys
from pathlib import Path

# Import the helper functions defined in ``code/config.py``.
# The module lives in the same package, so a plain import works.
from config import ensure_directories, get_config_summary

def main() -> None:
    """Create directories and emit a human‑readable summary."""
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
