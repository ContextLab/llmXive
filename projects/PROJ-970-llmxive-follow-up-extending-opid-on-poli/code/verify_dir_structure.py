"""
verify_dir_structure.py

This script verifies the project directory structure by enumerating
directories up to a specified depth from the repository root and
writing their relative POSIX paths to ``data/processed/dir_structure.txt``.

It is used to satisfy task **T001a**, which requires capturing a
directory‑tree listing that contains explicit path strings such as
``src/environment`` so that unit tests can perform simple substring
checks.
"""
import os
from pathlib import Path

from llmxive_toolkit import paths, get_logger

log = get_logger(__name__)

def _collect_directories(root: Path, max_depth: int = 3) -> list[str]:
    """
    Recursively collect directory paths relative to *root* up to *max_depth*.

    Parameters
    ----------
    root: Path
        The repository root.
    max_depth: int
        Maximum depth (0 = root itself, 1 = immediate children, etc.).
        Depth 3 is required to capture paths such as
        ``data/raw/synthetic_graphs``.

    Returns
    -------
    List[str]
        Relative POSIX‑style directory paths (e.g. ``src/environment``).
    """
    dirs: list[str] = []

    def _helper(current: Path, depth: int) -> None:
        if depth > max_depth:
            return
        for child in sorted(current.iterdir()):
            if child.is_dir():
                rel_path = child.relative_to(root).as_posix()
                dirs.append(rel_path)
                _helper(child, depth + 1)

    _helper(root, 0)
    return dirs

def main() -> None:
    """
    Write a plain‑text list of directory paths (up to depth 3) to
    ``data/processed/dir_structure.txt``.
    """
    root_path = paths.root
    log.info("Collecting directory structure from project root: %s", root_path)

    # Depth 3 ensures we capture nested directories required by the test.
    dir_list = _collect_directories(root_path, max_depth=3)

    output_path = paths.data("processed", "dir_structure.txt")
    # Ensure the parent directory exists (paths.data creates it)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Write each directory on its own line.
    output_path.write_text("\n".join(dir_list) + "\n")
    log.info("Directory structure written to %s", output_path)

if __name__ == "__main__":
    main()
