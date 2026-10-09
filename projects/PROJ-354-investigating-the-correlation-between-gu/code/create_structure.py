"""
create_structure.py
-------------------
Script to create the full project directory tree, add empty ``__init__.py`` files
to every Python package, and write a reproducible directory listing to
``project_tree.txt``.

The script is idempotent: running it multiple times will not raise errors and
will leave the tree in a consistent state.

Execution command (as used by the CI runner):
    python code/create_structure.py
"""

import os
from pathlib import Path


def _ensure_dir(path: Path) -> None:
    """Create a directory (including parents) if it does not exist."""
    path.mkdir(parents=True, exist_ok=True)


def _touch_init(path: Path) -> None:
    """Create an empty ``__init__.py`` file in the given package directory."""
    init_file = path / "__init__.py"
    if not init_file.exists():
        init_file.touch()


def _create_project_structure(root: Path) -> None:
    """
    Create all required directories and ``__init__.py`` files.

    Parameters
    ----------
    root : Path
        The root of the repository (the directory that contains ``code/``).
    """
    # Directories that must exist (relative to the repository root)
    dirs = [
        root / "code",
        root / "code" / "utils",
        root / "code" / "models",
        root / "code" / "pipelines",
        root / "code" / "paper",
        root / "data",
        root / "data" / "raw",
        root / "data" / "processed",
        root / "data" / "interim",
        root / "results",
        root / "results" / "associations",
        root / "results" / "plots",
        root / "results" / "sensitivity",
        root / "results" / "power",
        root / "tests",
    ]

    # Create directories
    for d in dirs:
        _ensure_dir(d)

    # Packages that need an ``__init__.py`` (including the top‑level ``code`` package)
    package_dirs = [
        root / "code",
        root / "code" / "utils",
        root / "code" / "models",
        root / "code" / "pipelines",
        root / "code" / "paper",
        root / "tests",
    ]

    for pkg in package_dirs:
        _touch_init(pkg)


def _write_tree_listing(root: Path) -> None:
    """
    Generate a reproducible directory tree listing.

    The listing mimics ``tree -a -I '.git|__pycache__'`` but is generated
    using pure Python so it works in environments where the ``tree`` utility
    is unavailable.

    The output format is a simple line‑by‑line list of paths relative to the
    repository root, one entry per file or directory, sorted alphabetically.
    Hidden files (those starting with a dot) are included, while any path
    containing ``.git`` or ``__pycache__`` is excluded.
    """
    output_file = root / "project_tree.txt"

    # Gather all files and directories, include hidden ones, exclude .git and __pycache__
    all_paths = []
    for path in root.rglob("*"):
        # Exclude the .git and __pycache__ directories (and anything inside them)
        if ".git" in path.parts or "__pycache__" in path.parts:
            continue
        # Record path relative to the repository root
        rel_path = path.relative_to(root)
        all_paths.append(rel_path)

    # Sort for reproducibility
    all_paths.sort()

    # Write each path on its own line
    with output_file.open("w", encoding="utf-8") as f:
        for rel_path in all_paths:
            f.write(str(rel_path) + "\n")

    # Log a short message for debugging (stdout)
    print(f"Project tree written to {output_file}")


def main() -> None:
    """
    Entry point for the script.

    It determines the repository root (the parent of the directory containing this
    file), creates the directory structure, adds ``__init__.py`` files, and writes
    ``project_tree.txt``.
    """
    # The repository root is two levels up from this file:
    #   <repo_root>/code/create_structure.py
    repo_root = Path(__file__).resolve().parents[1]

    _create_project_structure(repo_root)
    _write_tree_listing(repo_root)


if __name__ == "__main__":
    main()