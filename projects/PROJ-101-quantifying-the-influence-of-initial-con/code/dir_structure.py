"""
Directory Structure Generator for the project.

This script creates the required top‑level directory layout and records
the layout in a plain‑text file.  The layout file is written to
``data/processed/dir_structure.txt`` – a project‑owned location (the
original specification asked for ``state/dir_structure.txt`` but the
platform owns the ``state`` folder, so we store the file under
``data/processed`` instead).

The script can be executed directly:
    python code/dir_structure.py

It will create any missing directories and write the directory tree
(depth 2) to the output file.
"""

import os
from pathlib import Path
from llmxive_toolkit import paths, get_logger

log = get_logger(__name__)

# ----------------------------------------------------------------------
# Helper: generate a simple two‑level tree representation.
# ----------------------------------------------------------------------
def _generate_tree(root: Path) -> str:
    """
    Return a string representation of the directory tree under ``root``,
    limited to two levels (the root and its immediate sub‑directories).
    """
    lines = [str(root)]
    for entry in sorted(root.iterdir()):
        if entry.is_dir():
            lines.append(f"├── {entry.name}")
            # List sub‑directories of this entry (second level)
            sub_entries = sorted([e for e in entry.iterdir() if e.is_dir()])
            for i, sub in enumerate(sub_entries):
                prefix = "│   " if i < len(sub_entries) - 1 else "    "
                lines.append(f"{prefix}└── {sub.name}")
    return "\n".join(lines)

# ----------------------------------------------------------------------
# Main routine
# ----------------------------------------------------------------------
def generate_dir_structure() -> str:
    """
    Ensure the required directories exist and return a textual tree
    representation limited to two levels.
    """
    # Required top‑level directories (relative to the project root)
    required_dirs = [
        Path("code"),
        Path("code/simulation"),
        Path("code/analysis"),
        Path("code/utils"),
        Path("tests/unit"),
        Path("tests/integration"),
        Path("data/raw"),
        Path("data/processed"),
    ]

    # Create any missing directories using the llmxive ``paths`` helpers.
    for d in required_dirs:
        # ``paths.path`` creates the folder if it does not exist.
        # It returns a Path object inside the project root.
        paths.path(*d.parts)

    # Generate the tree representation.
    project_root = Path(__file__).resolve().parents[1]  # project root
    tree_str = _generate_tree(project_root)

    # Write the result to the designated output file.
    output_path = paths.data("processed", "dir_structure.txt")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(tree_str + "\n")
    log.info(f"Directory structure written to {output_path}")
    return tree_str

# ----------------------------------------------------------------------
# CLI entry point
# ----------------------------------------------------------------------
if __name__ == "__main__":
    generate_dir_structure()
