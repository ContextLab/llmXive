"""Create the required project directory hierarchy and capture tree listings.

This script creates all directories listed in the T001 task, then uses the
external ``tree`` command to generate a two‑level directory listing for the
``data`` hierarchy and for the ``outputs``/``docs`` hierarchy.  The listings
are written to ``data/data_dir_tree.txt`` and ``data/output_dir_tree.txt``
respectively.

The script is intended to be run as a standalone executable (``python
code/create_hierarchy.py``) and will exit with a non‑zero status if any
``tree`` invocation fails, satisfying the verification requirement.
"""
import subprocess
from pathlib import Path

from llmxive_toolkit import paths, get_logger

log = get_logger(__name__)

def create_directories() -> None:
    """Create all required directories for the project."""
    dirs = [
        Path("code/ingestion"),
        Path("code/processing"),
        Path("code/analysis"),
        Path("code/utils"),
        Path("code/tests"),
        Path("data/raw/tng100"),
        Path("data/raw/millennium"),
        Path("data/processed"),
        Path("outputs/figures"),
        Path("outputs/reports"),
        Path("docs"),
    ]
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)
        log.info(f"Created directory: {d}")

def capture_tree_outputs() -> None:
    """Run ``tree -L 2`` on the relevant top‑level directories and save output."""
    # Tree for the data hierarchy
    data_tree_path = paths.data("data_dir_tree.txt")
    with data_tree_path.open("w", encoding="utf-8") as f:
        subprocess.run(
            ["tree", "-L", "2", "data"],
            stdout=f,
            check=True,
        )
    log.info(f"Data hierarchy tree written to {data_tree_path}")

    # Tree for the outputs + docs hierarchy
    output_tree_path = paths.data("output_dir_tree.txt")
    with output_tree_path.open("w", encoding="utf-8") as f:
        subprocess.run(
            ["tree", "-L", "2", "outputs", "docs"],
            stdout=f,
            check=True,
        )
    log.info(f"Outputs/docs hierarchy tree written to {output_tree_path}")

def main() -> None:
    """Entry point."""
    create_directories()
    capture_tree_outputs()
    log.info("Project hierarchy creation and verification completed successfully.")

if __name__ == "__main__":
    main()
