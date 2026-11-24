"""
code/create_project_structure.py
Script to create the required project directory hierarchy for the
llmXive follow-up project and capture its layout using a simple
tree-like representation (depth 2). The layout is written to
`data/results/project_structure.txt`.

Note: the platform owns the top-level `state/` directory and derives
artifact hashes at verification time, so this script does NOT create
(and actively removes any shadow copy of) `state/` inside the project.
"""

import shutil
from pathlib import Path

from llmxive_toolkit import paths

# Base directory for the project hierarchy (relative to repository root)
BASE_DIR = Path("projects/PROJ-915-llmxive-follow-up-extending-measuring-ep")

# Sub-folders to create (relative to BASE_DIR).
# `state/` is intentionally excluded: it is platform-owned.
SUB_FOLDERS = [
    "code",
    "data/raw",
    "data/processed",
    "data/interim",
    "data/results",
    "tests/unit",
    "tests/integration",
    "docs",
]


def _project_root() -> Path:
    """Return the project root directory, whatever the current cwd is."""
    root = paths.root
    # paths.root is the project directory itself; BASE_DIR naming is
    # relative to the repository root, so the project dir IS the base.
    return root


def remove_shadow_state_dir() -> None:
    """Remove any shadow `state/` directory created inside the project.

    The platform owns `state/`; a copy inside the project is a stale
    shadow that the verifier would read instead of canonical state.
    """
    root = _project_root()
    shadow = root / "state"
    if shadow.is_dir():
        shutil.rmtree(shadow)
        print(f"Removed shadow platform-owned directory: {shadow}")


def create_directories() -> None:
    """Create all required (project-owned) directories."""
    root = _project_root()
    for sub in SUB_FOLDERS:
        dir_path = root / sub
        dir_path.mkdir(parents=True, exist_ok=True)


def generate_tree_output(max_depth: int = 2) -> str:
    """
    Generate a tree-like representation of the project up to ``max_depth``.
    This avoids reliance on the external ``tree`` command.
    """
    root = _project_root()
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
    _walk(root, "", 0)
    return "\n".join(lines)


def write_structure_file() -> None:
    """Write the tree output to the expected results file."""
    output_path = paths.data("results", "project_structure.txt")
    tree_text = generate_tree_output(max_depth=2)
    output_path.write_text(tree_text, encoding="utf-8")
    print(f"Project structure written to {output_path}")


def main() -> None:
    remove_shadow_state_dir()
    create_directories()
    write_structure_file()


if __name__ == "__main__":
    main()
