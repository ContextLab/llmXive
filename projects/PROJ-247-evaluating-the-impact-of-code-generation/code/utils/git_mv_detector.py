"""
Utility functions for detecting Git rename (mv) events for a file within a repository,
deciding whether a code block should be excluded based on rename semantics,
and logging/reporting the exclusions.
"""

import subprocess
import json
from pathlib import Path
from typing import List, Tuple, Dict

def _run_git_command(repo_path: Path, args: List[str]) -> str:
    """Run a git command inside ``repo_path`` and return stdout as text.

    Raises ``subprocess.CalledProcessError`` if the command fails.
    """
    result = subprocess.run(
        ["git", "-C", str(repo_path)] + args,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=True,
        text=True,
    )
    return result.stdout

def get_git_rename_history(repo_path: Path, file_path: Path) -> List[Tuple[str, str]]:
    """
    Return a list of rename tuples ``(old_path, new_path)`` for ``file_path`` as
    tracked by ``git log --follow``. Only rename entries (lines starting with ``R``)
    are returned.

    Parameters
    ----------
    repo_path: Path
        Path to the root of the git repository.
    file_path: Path
        Path to the file **relative to the repository root**.

    Returns
    -------
    List[Tuple[str, str]]
        Ordered list (old → new) of rename operations.
    """
    # ``--name-status`` prints lines like: "R100\told_path\tnew_path"
    raw = _run_git_command(
        repo_path,
        ["log", "--follow", "--pretty=format:", "--name-status", "--", str(file_path)],
    )
    renames: List[Tuple[str, str]] = []
    for line in raw.splitlines():
        if line.startswith("R"):
            parts = line.split("\t")
            if len(parts) == 3:
                _, old_path, new_path = parts
                renames.append((old_path, new_path))
    return renames

def _path_depth(p: str) -> int:
    """Return the number of path segments (depth) for a POSIX path."""
    return len(Path(p).parts)

def _parent_dir_name(p: str) -> str:
    """Return the immediate parent directory name of a POSIX path."""
    return Path(p).parent.name

def should_exclude_due_to_rename(old_path: str, new_path: str) -> bool:
    """
    Decide whether a rename should trigger exclusion of a code block.
    Exclusion criteria (per spec):
    - Change in directory depth (different number of path segments), OR
    - Change in the immediate parent directory name.

    Returns ``True`` if the block must be excluded.
    """
    if _path_depth(old_path) != _path_depth(new_path):
        return True
    if _parent_dir_name(old_path) != _parent_dir_name(new_path):
        return True
    return False

def log_exclusion(
    block_id: str,
    old_path: str,
    new_path: str,
    reason: str,
    log_file: Path,
) -> None:
    """
    Append a single exclusion line to ``log_file``.
    Format: ``block_id,old_path,new_path,reason`` (CSV).
    The file is created if it does not exist.
    """
    log_file.parent.mkdir(parents=True, exist_ok=True)
    with log_file.open("a", encoding="utf-8") as f:
        line = f"{block_id},{old_path},{new_path},{reason}\n"
        f.write(line)

def generate_validation_report(
    exclusions: List[Dict],
    report_path: Path,
) -> None:
    """
    Write a JSON validation report summarising the rename‑based exclusions.
    The JSON schema is a list of objects with keys:
    ``block_id``, ``old_path``, ``new_path``, ``reason``.
    """
    report_path.parent.mkdir(parents=True, exist_ok=True)
    with report_path.open("w", encoding="utf-8") as f:
        json.dump(exclusions, f, indent=2, ensure_ascii=False)
