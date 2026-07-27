#!/usr/bin/env python
"""
CI helper script that verifies the repository skeleton directories exist.
It uses the ``missing_directories`` function from ``check_skeleton`` to
determine which of the required top‑level directories are absent.
If any are missing the script exits with a non‑zero status, causing the CI
job to fail.
"""
import sys
from pathlib import Path

# Import the helper that returns a list of missing directories.
# ``check_skeleton`` lives at ``code/check_skeleton.py`` and is part of the
# project’s public API (see the provided API surface).
from check_skeleton import missing_directories


def main() -> None:
    """
    Execute the skeleton‑directory check.

    Prints a helpful error message to stderr and exits with status 1
    if any required directory is missing; otherwise exits with status 0.
    """
    # Resolve the project root (the directory containing this script's parent)
    # to make the check robust when the script is invoked from any working directory.
    project_root = Path(__file__).resolve().parents[2]

    # ``missing_directories`` is expected to look for the required folders
    # relative to the current working directory or a supplied root.  If it
    # accepts a path argument we pass the computed root; otherwise we rely
    # on its internal logic (which already uses the repository layout).
    try:
        missing = missing_directories()
    except TypeError:
        # Fallback: assume the function accepts a root path.
        missing = missing_directories(project_root)

    if missing:
        # Join the missing directory names for a concise message.
        missing_str = ", ".join(str(p) for p in missing)
        print(f"ERROR: Missing required repository skeleton directories: {missing_str}",
              file=sys.stderr)
        sys.exit(1)
    # Success – all required directories are present.
    sys.exit(0)


if __name__ == "__main__":
    main()