"""
Utilities for detecting and evaluating git rename events to determine
if a code block should be excluded from longitudinal analysis.
"""
import subprocess
from pathlib import Path
from typing import List, Tuple

def get_git_rename_history(repo_path: Path, rel_path: Path) -> List[Tuple[str, str]]:
    """
    Retrieve the history of renames for a given file using git log.
    Returns a list of (old_path, new_path) tuples.
    """
    try:
        # --name-status shows 'R100 old new' for renames
        # --follow continues tracking the file across renames
        result = subprocess.run(
            ["git", "log", "--follow", "--name-status", "--format=", "--", str(rel_path)],
            cwd=repo_path,
            capture_output=True,
            text=True,
            check=True,
        )
    except subprocess.CalledProcessError:
        return []

    renames = []
    for line in result.stdout.splitlines():
        line = line.strip()
        if not line:
            continue
        # Rename lines look like: R100  old_path  new_path
        if line.startswith("R"):
            parts = line.split(maxsplit=2)
            if len(parts) >= 3:
                # parts[0] is 'R100', parts[1] is old, parts[2] is new
                renames.append((parts[1], parts[2]))
    
    return renames

def should_exclude_due_to_rename(old_path_str: str, new_path_str: str) -> bool:
    """
    Determine if a rename event triggers exclusion based on the spec:
    Exclude if directory level changes (number of path segments) 
    or the immediate parent directory name changes.
    """
    p_old = Path(old_path_str)
    p_new = Path(new_path_str)

    # 1. Check directory level (depth)
    if len(p_old.parts) != len(p_new.parts):
        return True

    # 2. Check immediate parent directory name
    if p_old.parent.name != p_new.parent.name:
        return True

    return False
