"""
Utilities for detecting git rename (move) events for a file.
Provides functions to retrieve the rename history of a file within a repository
and to decide whether a rename should trigger exclusion based on directory
depth or parent directory name changes.
"""

from pathlib import Path
import subprocess
from typing import List, Tuple


def get_git_rename_history(repo_path: Path, rel_file: Path) -> List[Tuple[str, str]]:
    """
    Return a list of (old_path, new_path) tuples representing rename events
    for ``rel_file`` within the repository located at ``repo_path``.

    The function uses ``git log --follow`` with ``--name-status`` to capture
    rename entries (lines that start with ``R``).  Paths are returned as
    POSIX‑style strings (as emitted by git).  If the repository is not a
    valid git repository or git fails, an empty list is returned.

    Parameters
    ----------
    repo_path: Path
        Path to the root of the git repository.
    rel_file: Path
        Path to the file *relative* to ``repo_path`` whose rename history
        is being queried.

    Returns
    -------
    List[Tuple[str, str]]
        A list of rename pairs in chronological order (old → new).  If
        no renames are found, the list is empty.
    """
    try:
        result = subprocess.run(
            [
                "git",
                "log",
                "--follow",
                "--name-status",
                "--pretty=format:",
                "--",
                str(rel_file),
            ],
            cwd=repo_path,
            capture_output=True,
            text=True,
            check=True,
        )
    except subprocess.CalledProcessError:
        # Not a git repo or other git error – treat as no history.
        return []

    rename_pairs: List[Tuple[str, str]] = []
    for line in result.stdout.splitlines():
        line = line.strip()
        if not line:
            continue
        # Rename lines start with 'R' (e.g., 'R100\told.py\tnew.py')
        if line.startswith("R"):
            parts = line.split("\t")
            if len(parts) == 3:
                _, old_path, new_path = parts
                rename_pairs.append((old_path, new_path))
    return rename_pairs


def should_exclude_due_to_rename(old_path: str, new_path: str) -> bool:
    """
    Determine whether a rename event should cause exclusion of a code block.

    According to the specification, a block must be excluded if the rename
    changes either:
    * the directory depth (i.e., the number of path components), or
    * the immediate parent directory name.

    Parameters
    ----------
    old_path: str
        The original relative file path before the rename.
    new_path: str
        The new relative file path after the rename.

    Returns
    -------
    bool
        ``True`` if the rename meets an exclusion criterion, ``False`` otherwise.
    """
    old = Path(old_path)
    new = Path(new_path)

    # Depth comparison (number of parts in the path)
    if len(old.parts) != len(new.parts):
        return True

    # Immediate parent directory name comparison
    if old.parent.name != new.parent.name:
        return True

    return False
