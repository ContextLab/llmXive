"""
setup_skeleton.py

This script creates the canonical project directory tree required for the
"Predicting Molecular Properties from Vibrational Spectra" feature, adds empty
``__init__.py`` files so that the directories are recognised as Python packages,
and writes a sorted list of all directories to ``results/structure_report.txt``.

The script is idempotent: running it multiple times will not overwrite existing
files (except the structure report, which is regenerated each run).
"""

import sys
import compileall
from pathlib import Path
import logging

# ----------------------------------------------------------------------
# Define the directory structure (relative to the project root)
# ----------------------------------------------------------------------
DIRS = [
    Path("code"),
    Path("code/data"),
    Path("code/models"),
    Path("code/evaluation"),
    Path("code/utils"),
    Path("tests"),
    Path("data/raw"),
    Path("data/processed"),
    Path("data/external"),
    Path("results"),
    Path("logs"),
    Path("specs/001-predict-molecular-properties"),
    Path("specs/001-predict-molecular-properties/contracts"),
]

# ----------------------------------------------------------------------
# Helper to create a directory and an empty __init__.py if it is a Python
# package (i.e., under ``code/`` or ``tests/`` or ``specs/...``)
# ----------------------------------------------------------------------
def ensure_dir(path: Path) -> None:
    """Create *path* (including parents) and an ``__init__.py`` if appropriate."""
    if not path.exists():
        path.mkdir(parents=True, exist_ok=True)
        # Create an empty __init__.py for packages
        if any(str(path).startswith(p) for p in ("code", "tests", "specs")):
            init_file = path / "__init__.py"
            init_file.touch(exist_ok=True)

# ----------------------------------------------------------------------
# Main execution
# ----------------------------------------------------------------------
def main() -> int:
    # 1. Create all required directories and ``__init__.py`` files
    for d in DIRS:
        ensure_dir(d)

    # 2. Write a sorted list of all directories in the repository.
    #    We use pathlib to avoid reliance on external ``find``.
    all_dirs = [
        str(p.relative_to(Path.cwd()))
        for p in Path(".").rglob("*")
        if p.is_dir()
    ]
    all_dirs.sort()

    # 3. Write the directory list to ``results/structure_report.txt``.
    #    The ``paths`` helper from ``llmxive_toolkit`` ensures the folder exists.
    try:
        from llmxive_toolkit import paths
        report_path = paths.results("structure_report.txt")
    except Exception:
        # Fallback if the toolkit is unavailable – create the path manually.
        report_path = Path("results") / "structure_report.txt"
        report_path.parent.mkdir(parents=True, exist_ok=True)

    with report_path.open("w", encoding="utf-8") as f:
        for line in all_dirs:
            f.write(line + "\n")

    return 0

if __name__ == "__main__":
    sys.exit(main())