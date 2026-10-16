"""
Script to create the required top‑level directory layout for the project
and record it in a text file. The layout is written under the project
root (not under the platform‑owned ``state/`` directory) to respect the
repository ownership rules. The resulting file ``data/dir_structure.txt``
contains a simple tree‑like listing of the directories (depth 2).
"""

import sys
from pathlib import Path

def _create_directories(root: Path, dirs: list[str]) -> None:
    """Create each directory in ``dirs`` relative to ``root``."""
    for d in dirs:
        (root / d).mkdir(parents=True, exist_ok=True)

def _write_tree_listing(root: Path, dirs: list[str], out_path: Path) -> None:
    """
    Write a minimal ``tree -L 2`` style listing.

    The format is:
        dir
          subdir
          subdir
    for each top‑level directory.
    """
    lines: list[str] = []
    for d in dirs:
        lines.append(d)
        sub_path = root / d
        if sub_path.is_dir():
            subdirs = sorted([p.name for p in sub_path.iterdir() if p.is_dir()])
            for sub in subdirs:
                lines.append(f"  {sub}")
    out_path.write_text("\n".join(lines))

def main() -> None:
    # Project root – two levels up from this file (code/create_dir_structure.py)
    project_root = Path(__file__).resolve().parents[1]

    # Required directories (as specified in the task)
    required_dirs = [
        "code",
        "code/simulation",
        "code/analysis",
        "code/utils",
        "tests/unit",
        "tests/integration",
        "data/raw",
        "data/processed",
        "state",
    ]

    # 1️⃣ Create the directories
    _create_directories(project_root, required_dirs)

    # 2️⃣ Record the layout in a file under a project‑owned folder
    output_file = project_root / "data" / "dir_structure.txt"
    _write_tree_listing(project_root, required_dirs, output_file)

    print(f"Directory layout written to {output_file}")

if __name__ == "__main__":
    main()
