"""
create_layout.py

Script to create the required top‑level directory layout for the
`001-crack-propagation-ml` feature and print a simple tree view for
verification.

Expected layout:

projects/
  001-crack-propagation-ml/
    code/
    data/
    tests/
    specs/
    contracts/
"""

import os
from pathlib import Path

def _create_dirs(base: Path, subfolders):
    """Create each subfolder under ``base`` if it does not already exist."""
    for sub in subfolders:
        dir_path = base / sub
        dir_path.mkdir(parents=True, exist_ok=True)

def _print_tree(start_path: Path, prefix: str = ""):
    """Recursively print a simple tree representation of directories."""
    entries = sorted([e for e in start_path.iterdir() if e.is_dir()])
    for idx, entry in enumerate(entries):
        connector = "└── " if idx == len(entries) - 1 else "├── "
        print(f"{prefix}{connector}{entry.name}")
        # Recurse with updated prefix
        extension = "    " if idx == len(entries) - 1 else "│   "
        _print_tree(entry, prefix + extension)

def main():
    # The script resides in: <repo_root>/projects/001-crack-propagation-ml/
    script_path = Path(__file__).resolve()
    project_root = script_path.parent  # projects/001-crack-propagation-ml

    subfolders = ["code", "data", "tests", "specs", "contracts"]
    _create_dirs(project_root, subfolders)

    print("\nDirectory layout created under:", project_root)
    print("\nTree view of the new layout:")
    print(project_root.name + "/")
    _print_tree(project_root)

if __name__ == "__main__":
    main()