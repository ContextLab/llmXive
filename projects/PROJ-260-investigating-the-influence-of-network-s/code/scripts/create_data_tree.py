#!/usr/bin/env python3
"""
Script to create the required data directory hierarchy for the project
and write a machine‑generated tree listing to ``docs/design/data_tree.txt``.

The directories created are:
  - data/raw/
  - data/derived/
  - data/derived/topology/
  - data/derived/vdos/
  - data/derived/reference/
  - data/derived/correlation/
  - data/metadata/

The file ``docs/design/data_tree.txt`` will contain the above seven
directories, one per line, in the order listed.
"""

import sys
from pathlib import Path


def main() -> None:
    # Define the directories that must exist
    dirs = [
        Path("data/raw"),
        Path("data/derived"),
        Path("data/derived/topology"),
        Path("data/derived/vdos"),
        Path("data/derived/reference"),
        Path("data/derived/correlation"),
        Path("data/metadata"),
    ]

    # Ensure each directory exists (create parents as needed)
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)

    # Ensure the docs/design directory exists for the output file
    design_dir = Path("docs/design")
    design_dir.mkdir(parents=True, exist_ok=True)

    # Write the tree listing (one directory per line)
    tree_file = design_dir / "data_tree.txt"
    with tree_file.open("w", encoding="utf-8") as f:
        for d in dirs:
            f.write(str(d) + "\n")

    print(f"Created required directories and wrote tree to {tree_file}", file=sys.stderr)


if __name__ == "__main__":
    main()
