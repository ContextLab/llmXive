"""
Git rename detection utilities.

Provides:
  - get_git_rename_history(repo_path, file_path)
  - should_exclude_due_to_rename(old_path, new_path)

These are used by the unit tests in ``tests/unit/test_git_mv_detection.py`` and
by the code‑block extraction pipeline.
"""

import subprocess
from pathlib import Path
from typing import List, Tuple


def get_git_rename_history(repo_path: Path, file_path: Path) -> List[Tuple[str, str]]:
    """
    Return a list of ``(old_path, new_path)`` tuples representing rename events
    for *file_path* within *repo_path*.

    The function runs ``git log --follow --name-status`` and parses lines that
    start with ``R`` (rename). The order of the list follows the chronological
    order of the log (oldest first).
    """
    try:
        result = subprocess.run(
            [
                "git",
                "log",
                "--follow",
                "--pretty=format:",
                "--name-status",
                str(file_path),
            ],
            cwd=repo_path,
            capture_output=True,
            text=True,
            check=True,
        )
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"Git log failed for {file_path} in {repo_path}: {e}") from e

    history: List[Tuple[str, str]] = []
    for line in result.stdout.splitlines():
        parts = line.split("\t")
        if not parts:
            continue
        status = parts[0]
        if status.startswith("R") and len(parts) >= 3:
            old, new = parts[1], parts[2]
            history.append((old, new))
    return history


def should_exclude_due_to_rename(old_path: str, new_path: str) -> bool:
    """
    Determine whether a rename should trigger exclusion.

    Exclusion criteria:
      * The directory depth (number of path components) changes.
      * The immediate parent directory name changes.

    Returns ``True`` if either condition holds.
    """
    old_parts = Path(old_path).parts
    new_parts = Path(new_path).parts

    # Depth comparison (ignore the filename)
    old_depth = len(old_parts) - 1
    new_depth = len(new_parts) - 1
    if old_depth != new_depth:
        return True

    # Parent directory name comparison
    old_parent = Path(old_path).parent.name
    new_parent = Path(new_path).parent.name
    if old_parent != new_parent:
        return True

    return False


__all__ = ["get_git_rename_history", "should_exclude_due_to_rename"]