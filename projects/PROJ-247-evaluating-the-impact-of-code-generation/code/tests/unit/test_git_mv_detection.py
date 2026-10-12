"""
Unit tests for the rename‑detection utilities used in T003.
The tests create a temporary git repository, perform file moves/renames,
and assert that the detection logic behaves as specified.
"""

import os
import subprocess
import tempfile
from pathlib import Path

import pytest

from utils.git_mv_detector import (
    get_git_rename_history,
    should_exclude_due_to_rename,
)

@pytest.fixture
def temp_repo():
    """Create a temporary git repository with an initial commit."""
    with tempfile.TemporaryDirectory() as td:
        repo = Path(td)
        subprocess.run(["git", "init"], cwd=repo, check=True, stdout=subprocess.DEVNULL)
        # Configure user (required for commits)
        subprocess.run(
            ["git", "config", "user.email", "test@example.com"],
            cwd=repo,
            check=True,
            stdout=subprocess.DEVNULL,
        )
        subprocess.run(
            ["git", "config", "user.name", "Test User"],
            cwd=repo,
            check=True,
            stdout=subprocess.DEVNULL,
        )
        # Create a file and commit it
        (repo / "a.py").write_text("def foo():\n    pass\n")
        subprocess.run(["git", "add", "."], cwd=repo, check=True)
        subprocess.run(["git", "commit", "-m", "initial"], cwd=repo, check=True)

        yield repo

def test_no_rename_detected(temp_repo: Path):
    """A file that never moves should yield an empty rename history."""
    history = get_git_rename_history(temp_repo, Path("a.py"))
    assert history == []

def test_simple_rename_same_dir(temp_repo: Path):
    """Renaming within the same directory should be detected but NOT excluded."""
    # Rename a.py -> b.py
    subprocess.run(["git", "mv", "a.py", "b.py"], cwd=temp_repo, check=True)
    (temp_repo / "b.py").write_text("def foo():\n    pass\n")  # ensure content unchanged
    subprocess.run(["git", "commit", "-m", "rename a.py to b.py"], cwd=temp_repo, check=True)

    history = get_git_rename_history(temp_repo, Path("b.py"))
    assert history == [("a.py", "b.py")]
    # Depth unchanged, parent unchanged → should not trigger exclusion
    assert not should_exclude_due_to_rename("a.py", "b.py")

def test_move_to_subdirectory(temp_repo: Path):
    """Moving a file into a subdirectory changes depth → exclusion."""
    subdir = temp_repo / "sub"
    subdir.mkdir()
    subprocess.run(["git", "mv", "a.py", "sub/a.py"], cwd=temp_repo, check=True)
    subprocess.run(["git", "commit", "-m", "move a.py into sub"], cwd=temp_repo, check=True)

    history = get_git_rename_history(temp_repo, Path("sub/a.py"))
    assert history == [("a.py", "sub/a.py")]
    assert should_exclude_due_to_rename("a.py", "sub/a.py")

def test_move_to_different_parent_same_depth(temp_repo: Path):
    """Moving a file to a sibling directory changes parent name → exclusion."""
    (temp_repo / "dir1").mkdir()
    (temp_repo / "dir2").mkdir()
    # Move a.py into dir1 first (to have a path we can later move)
    subprocess.run(["git", "mv", "a.py", "dir1/a.py"], cwd=temp_repo, check=True)
    subprocess.run(["git", "commit", "-m", "move to dir1"], cwd=temp_repo, check=True)
    # Now move from dir1 to dir2 (same depth, different parent)
    subprocess.run(["git", "mv", "dir1/a.py", "dir2/a.py"], cwd=temp_repo, check=True)
    subprocess.run(["git", "commit", "-m", "move to dir2"], cwd=temp_repo, check=True)

    history = get_git_rename_history(temp_repo, Path("dir2/a.py"))
    # Expect two rename entries; we only need the last one for the check
    assert ("dir1/a.py", "dir2/a.py") in history
    assert should_exclude_due_to_rename("dir1/a.py", "dir2/a.py")
