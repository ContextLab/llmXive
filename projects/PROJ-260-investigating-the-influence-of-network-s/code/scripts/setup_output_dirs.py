"""
Script to set up the output directory hierarchy for the project and
document the structure in `docs/design/output_tree.txt`.

This fulfills task T002:
  * Create directories: outputs/, outputs/figures/, outputs/reports/
  * Write a plain‑text tree listing of these directories to
    docs/design/output_tree.txt (one path per line).

The script is deliberately tiny and has no external dependencies beyond the
Python standard library, so it can be run on any CI runner.
"""

import os
from pathlib import Path
import sys

# ----------------------------------------------------------------------
# Configuration
# ----------------------------------------------------------------------
# Root of the repository (the directory containing this script's parent)
PROJECT_ROOT = Path(__file__).resolve().parents[2]

# Desired output directories (relative to PROJECT_ROOT)
OUTPUT_DIRS = [
    Path("outputs"),
    Path("outputs") / "figures",
    Path("outputs") / "reports",
]

# Documentation file that will contain the hierarchy listing
HIERARCHY_DOC = PROJECT_ROOT / "docs" / "design" / "output_tree.txt"


def create_directories() -> None:
    """
    Create the required output directories.  Missing parent directories are
    created automatically (e.g., `outputs/` is created before its children).
    """
    for dir_path in OUTPUT_DIRS:
        full_path = PROJECT_ROOT / dir_path
        full_path.mkdir(parents=True, exist_ok=True)


def write_hierarchy_doc() -> None:
    """
    Write a plain‑text file listing each output directory on its own line.
    The file is written to ``docs/design/output_tree.txt`` as required by
    the task specification.
    """
    # Ensure the parent directory exists
    HIERARCHY_DOC.parent.mkdir(parents=True, exist_ok=True)

    # Write the hierarchy – one entry per line, using POSIX‑style separators
    with HIERARCHY_DOC.open("w", encoding="utf-8") as f:
        for dir_path in OUTPUT_DIRS:
            # Store the path relative to the repository root
            f.write(f"{dir_path.as_posix()}/\n")


def main() -> None:
    """
    Entry point for the script.  It creates the directories and then
    writes the documentation file.
    """
    create_directories()
    write_hierarchy_doc()
    # Provide a tiny confirmation for manual runs
    print(f"Created output directories and wrote hierarchy to {HIERARCHY_DOC}")


if __name__ == "__main__":
    # When executed directly, run the main routine.
    # Any unexpected exception will cause a non‑zero exit code,
    # which satisfies the “fail loudly” requirement.
    main()
