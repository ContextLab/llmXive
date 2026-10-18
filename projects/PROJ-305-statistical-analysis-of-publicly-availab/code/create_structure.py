"""
Project Structure Setup Script
===============================

This script creates the required directory layout for the VAERS
statistical analysis project and writes a snapshot of the first three
levels of the repository tree to ``logs/structure.txt``.  It uses the
system ``tree`` command when available and falls back to ``find`` if
``tree`` is not installed.

The script is intended to be run as an entry point:

    python -m code.create_structure
"""

import subprocess
import sys
from pathlib import Path

from llmxive_toolkit import paths, get_logger

# ----------------------------------------------------------------------
# Logger
# ----------------------------------------------------------------------
log = get_logger(__name__)  # optional: get_logger(__name__, log_file="logs/run.log")

# ----------------------------------------------------------------------
# Required directory list (matches the task specification)
# ----------------------------------------------------------------------
REQUIRED_DIRS = [
    "src/data",
    "src/analysis",
    "src/utils",
    "src/validation",
    "tests/unit",
    "tests/integration",
    "tests/fixtures",
    "data/raw",
    "data/processed",
    "data/results",
    "output/figures",
    "output/temporal_profiles",
    "logs",
]


def create_directories() -> None:
    """Create every directory in ``REQUIRED_DIRS`` (including parents)."""
    for d in REQUIRED_DIRS:
        Path(d).mkdir(parents=True, exist_ok=True)
    log.info(f"Created {len(REQUIRED_DIRS)} required directories.")


def write_structure_snapshot() -> None:
    """
    Capture a three‑level directory listing.

    Primary method: ``tree -a -L 3``.
    Fallback: ``find . -maxdepth 3 -type d``.
    The result is written to ``logs/structure.txt`` using the
    ``llmxive_toolkit.paths`` helper (which also creates the parent folder).
    """
    output_path = paths.logs("structure.txt")
    output_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        # ``tree`` prints a nicely‑formatted hierarchy.
        result = subprocess.run(
            ["tree", "-a", "-L", "3"],
            capture_output=True,
            text=True,
            check=True,
        )
        content = result.stdout
        log.info("Directory snapshot generated via `tree`.")
    except (FileNotFoundError, subprocess.CalledProcessError):
        # ``tree`` not installed or failed – use ``find`` as a reliable fallback.
        log.warning("`tree` command unavailable; falling back to `find`.")
        result = subprocess.run(
            ["find", ".", "-maxdepth", "3", "-type", "d"],
            capture_output=True,
            text=True,
            check=True,
        )
        # ``find`` returns one directory per line; join with newlines.
        content = "\n".join(result.stdout.splitlines())

    output_path.write_text(content, encoding="utf-8")
    log.info(f"Wrote directory structure snapshot to {output_path}")


def main() -> None:
    """Entry point used by ``python -m code.create_structure``."""
    create_directories()
    write_structure_snapshot()


if __name__ == "__main__":
    # Allow direct execution as ``python code/create_structure.py``.
    main()
