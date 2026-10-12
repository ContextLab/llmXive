"""
code/create_project_structure.py
Script to create the required project directory hierarchy for the
llmXive follow‑up project and capture its layout using a simple
tree‑like representation (depth 2). The layout is written to
`data/results/project_structure.txt`.
"""

import os
from pathlib import Path
import json

# Base directory for the project hierarchy
BASE_DIR = Path("projects/PROJ-915-llmxive-follow-up-extending-measuring-ep")

# Sub‑folders to create (relative to BASE_DIR)
SUB_FOLDERS = [
    "code",
    "data/raw",
    "data/processed",
    "data/interim",
    "data/results",
    "state",
    "tests/unit",
    "tests/integration",
    "docs",
]

def create_directories() -> None:
    """Create all required directories."""
    for sub in SUB_FOLDERS:
        dir_path = BASE_DIR / sub
        dir_path.mkdir(parents=True, exist_ok=True)

def generate_tree_output(max_depth: int = 2) -> str:
    """
    Generate a tree‑like representation of BASE_DIR up to ``max_depth``.
    This avoids reliance on the external ``tree`` command.
    """
    lines = []

    def _walk(current_path: Path, prefix: str = "", depth: int = 0):
        if depth > max_depth:
            return
        entries = sorted([p for p in current_path.iterdir() if p.is_dir()])
        for i, entry in enumerate(entries):
            connector = "├── " if i < len(entries) - 1 else "└── "
            line = f"{prefix}{connector}{entry.name}"
            lines.append(line)
            if depth < max_depth - 1:
                extension = "│   " if i < len(entries) - 1 else "    "
                _walk(entry, prefix + extension, depth + 1)

    # Root line (relative to repository root)
    lines.append(str(BASE_DIR))
    _walk(BASE_DIR, "", 0)
    return "\n".join(lines)

def write_structure_file() -> None:
    """Write the tree output to the expected results file."""
    output_path = Path("data/results/project_structure.txt")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    tree_text = generate_tree_output(max_depth=2)
    output_path.write_text(tree_text, encoding="utf-8")
    print(f"Project structure written to {output_path}")

def main() -> None:
    create_directories()
    write_structure_file()

if __name__ == "__main__":
    main()
