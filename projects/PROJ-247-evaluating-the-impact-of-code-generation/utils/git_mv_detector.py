"""
Utilities for detecting rename (git mv) history of a file within a Git repository
and deciding whether a rename should cause exclusion of a code block.

The functions are used by the code‑block‑extraction script (``code/03_code_block_extraction.py``)
and by unit tests (``code/tests/unit/test_git_mv_detection.py``).
"""

import subprocess
from pathlib import Path
from typing import List, Tuple

def get_git_rename_history(repo_path: Path, rel_file: Path) -> List[Tuple[str, str]]:
    """
    Return a list of rename events for ``rel_file`` within ``repo_path``.

    Each rename event is a tuple ``(old_path, new_path)`` where the paths are
    relative to the repository root (the same style as ``rel_file``).

    The implementation relies on ``git log --follow --summary`` which
    reports rename operations in lines that start with ``R`` (e.g.
    ``R100\told_path\tnew_path``).  The function parses those lines,
    preserving the order in which Git reports them (chronological from
    oldest to newest).

    Parameters
    ----------
    repo_path: Path
        Path to the root of the Git repository.
    rel_file: Path
        Path to the file *as it exists now*, relative to ``repo_path``.

    Returns
    -------
    List[Tuple[str, str]]
        A list of rename pairs.  If the file has never been renamed, the
        list is empty.
    """
    # Ensure we are working with absolute paths for the subprocess call
    repo_path = repo_path.resolve()
    rel_file = rel_file.as_posix()  # git expects POSIX style paths

    try:
        result = subprocess.run(
            [
                "git",
                "log",
                "--follow",
                "--summary",
                "--format=%H",  # commit hash only (helps git separate commits)
                "--",
                rel_file,
            ],
            cwd=repo_path,
            capture_output=True,
            text=True,
            check=True,
        )
    except subprocess.CalledProcessError as e:
        # If git fails (e.g., not a git repo), re‑raise to make the failure loud.
        raise RuntimeError(f"Git log failed for {repo_path}/{rel_file}: {e}") from e

    rename_events: List[Tuple[str, str]] = []
    # The output interleaves commit hashes and summary lines.
    # We only care about lines that start with 'R' (rename).
    for line in result.stdout.splitlines():
        line = line.strip()
        if not line:
            continue
        # Rename lines look like: "R100\told_path\tnew_path"
        if line.startswith("R"):
            parts = line.split("\t")
            if len(parts) >= 3:
                _, old_path, new_path = parts[:3]
                rename_events.append((old_path, new_path))
    return rename_events

def should_exclude_due_to_rename(old_path: str, new_path: str) -> bool:
    """
    Decide whether a rename should trigger exclusion of a code block.

    Exclusion criteria (as defined in the task specification):
    * The directory depth changes (e.g., moving a file into a sub‑directory).
    * The immediate parent directory name changes, even if the depth stays the same
      (e.g., moving ``dir1/file.py`` to ``dir2/file.py``).

    Parameters
    ----------
    old_path: str
        The original file path (relative to the repository root) before the rename.
    new_path: str
        The new file path (relative to the repository root) after the rename.

    Returns
    -------
    bool
        ``True`` if the rename meets any exclusion criterion, ``False`` otherwise.
    """
    old_parts = Path(old_path).parts
    new_parts = Path(new_path).parts

    # Depth is number of directories (parts minus the file name)
    old_depth = len(old_parts) - 1
    new_depth = len(new_parts) - 1

    if old_depth != new_depth:
        return True

    # Compare immediate parent directory names
    old_parent = Path(old_path).parent.name
    new_parent = Path(new_path).parent.name
    if old_parent != new_parent:
        return True

    return False