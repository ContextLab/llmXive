"""
check_skeleton.py

This script is used in CI to verify that the repository skeleton directories
required by the project exist. If any of the required directories are missing,
the script exits with a non‑zero status code, causing the CI step to fail.

Required skeleton directories (relative to the repository root):
  - src
  - tests
  - data
  - results
  - docs
  - contracts
"""

import sys
from pathlib import Path
from typing import List


# List of directories that must exist at the repository root
REQUIRED_DIRECTORIES: List[Path] = [
    Path("src"),
    Path("tests"),
    Path("data"),
    Path("results"),
    Path("docs"),
    Path("contracts"),
]


def missing_directories() -> List[Path]:
    """
    Return a list of required directories that are missing.

    The check is performed relative to the current working directory,
    which in CI is the repository root.
    """
    return [d for d in REQUIRED_DIRECTORIES if not d.is_dir()]


def main() -> None:
    """
    Entry point for the script.

    Prints a concise report to stdout/stderr and exits with:
      - 0 if all required directories are present
      - 1 if any required directory is missing
    """
    missing = missing_directories()
    if missing:
        # Report each missing directory on its own line for easy parsing
        for d in missing:
            print(f"Missing required directory: {d}", file=sys.stderr)
        # Use a distinct exit code to signal the failure in CI
        sys.exit(1)
    else:
        print("All required skeleton directories are present.")
        sys.exit(0)


if __name__ == "__main__":
    main()