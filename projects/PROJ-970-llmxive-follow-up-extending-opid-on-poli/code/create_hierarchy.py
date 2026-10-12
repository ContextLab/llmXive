#!/usr/bin/env python3
"""
T001 – Create project folder hierarchy

This script creates the required directory structure for the OPID
critical‑first routing complexity analysis project, places a placeholder
README.md in each folder, runs ``tree -L 2`` on the repository root,
and writes the resulting directory listing to
``data/processed/dir_structure.txt``.
"""

import subprocess
import sys
from pathlib import Path

def _project_root() -> Path:
    """
    Return the repository root directory assuming this script lives in
    ``code/`` (one level below the root).
    """
    return Path(__file__).resolve().parent.parent

def _create_dirs(root: Path) -> None:
    """
    Create all required directories and a placeholder README.md in each.
    """
    # Base directories required by the specification
    dirs = [
        Path("src"),
        Path("src/environment"),
        Path("src/agent"),
        Path("src/simulation"),
        Path("src/analysis"),
        Path("src/utils"),
        Path("tests"),
        Path("data/raw/synthetic_graphs"),
        Path("data/processed"),
    ]

    for rel_path in dirs:
        dir_path = root / rel_path
        dir_path.mkdir(parents=True, exist_ok=True)

        readme_path = dir_path / "README.md"
        if not readme_path.is_file():
            readme_path.write_text(
                f"# {rel_path}\n\n"
                "Placeholder README for the directory. This file exists only to\n"
                "ensure the directory is tracked by version control.\n"
            )

def _run_tree(root: Path) -> str:
    """
    Execute ``tree -L 2`` on the repository root and return its stdout.
    Raises a clear error if the ``tree`` command is unavailable.
    """
    try:
        completed = subprocess.run(
            ["tree", "-L", "2", str(root)],
            capture_output=True,
            text=True,
            check=True,
        )
        return completed.stdout
    except FileNotFoundError:
        sys.exit(
            "The ``tree`` command was not found. Install it (e.g., ``apt-get install tree``) "
            "or ensure it is on the PATH before running this script."
        )
    except subprocess.CalledProcessError as exc:
        sys.exit(f"tree command failed with exit code {exc.returncode}: {exc.stderr}")

def _write_output(root: Path, content: str) -> None:
    """
    Write the tree output to ``data/processed/dir_structure.txt``.
    """
    out_path = root / "data/processed/dir_structure.txt"
    out_path.write_text(content)

def main() -> None:
    root = _project_root()
    _create_dirs(root)
    tree_output = _run_tree(root)
    _write_output(root, tree_output)
    print(f"Directory structure written to {root / 'data/processed/dir_structure.txt'}")

if __name__ == "__main__":
    main()