"""
Project Structure Creation Script
=================================

This script creates the required directory layout for the VAERS statistical
analysis project and writes a snapshot of the filesystem hierarchy to
``logs/structure.txt``.  It first attempts to use the external ``tree``
command (``tree -a -L 3``).  If ``tree`` is unavailable or fails, a pure‑Python
fallback walks the directory tree up to three levels deep and writes a
simple list of directories (each ending with a slash).

The script is intended to be executed via::

    python -m code.create_structure

which satisfies the verification step in task T001 (the existence of
``logs/structure.txt`` and the presence of the required directories).

The implementation relies only on the standard library and the
``llmxive_toolkit`` helpers for path handling and logging.
"""

import os
import subprocess
import sys
from pathlib import Path

from llmxive_toolkit import paths, get_logger

# ----------------------------------------------------------------------
# Logger
# ----------------------------------------------------------------------
log = get_logger(__name__)

# ----------------------------------------------------------------------
# Required directories (relative to the repository root)
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

# ----------------------------------------------------------------------
# Helper: create all directories
# ----------------------------------------------------------------------
def create_directories() -> None:
    """Create each directory in ``REQUIRED_DIRS`` (including parents)."""
    for rel_dir in REQUIRED_DIRS:
        dir_path = Path(rel_dir)
        dir_path.mkdir(parents=True, exist_ok=True)
        log.debug(f"Ensured directory exists: {dir_path}")

# ----------------------------------------------------------------------
# Helper: write a snapshot of the directory tree to logs/structure.txt
# ----------------------------------------------------------------------
def write_structure_snapshot() -> None:
    """
    Capture a three‑level directory listing.

    Primary method uses ``tree -a -L 3``.  If the command is missing or
    returns a non‑zero exit status, a Python fallback walks the file system.
    The result is written to ``logs/structure.txt`` using the
    ``llmxive_toolkit.paths`` helper.
    """
    output_path = paths.logs("structure.txt")
    output_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        # ``tree`` prints the full tree rooted at the current working directory.
        result = subprocess.run(
            ["tree", "-a", "-L", "3", "."],
            capture_output=True,
            text=True,
            check=True,
        )
        content = result.stdout
        log.info("Directory snapshot captured using the 'tree' command.")
    except (FileNotFoundError, subprocess.CalledProcessError) as e:
        log.warning(
            f"'tree' command unavailable or failed ({e}); using Python fallback."
        )
        # Python fallback: list directories up to depth 3
        max_depth = 3
        lines = []
        root = Path.cwd()
        for dirpath, dirnames, _ in os.walk(root):
            rel_path = Path(dirpath).relative_to(root)
            depth = len(rel_path.parts)
            if depth <= max_depth:
                # Ensure a trailing slash to indicate a directory
                lines.append(str(rel_path) + "/" if str(rel_path) else "./")
        content = "\n".join(lines) + "\n"
        log.info("Directory snapshot generated via Python fallback.")

    # Write the snapshot
    output_path.write_text(content, encoding="utf-8")
    log.info(f"Wrote directory structure to {output_path}")

# ----------------------------------------------------------------------
# Main entry point
# ----------------------------------------------------------------------
def main() -> None:
    """Create directories and write the structure log."""
    log.info("Starting project layout creation (T001).")
    create_directories()
    write_structure_snapshot()
    log.info("Project layout creation completed successfully.")

if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        log.error(f"Unexpected error during setup: {exc}")
        sys.exit(1)