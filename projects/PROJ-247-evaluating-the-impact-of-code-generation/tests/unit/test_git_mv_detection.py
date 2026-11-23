"""
Unit tests for the rename-detection utilities used in T003.
"""
import os
import subprocess
import tempfile
from pathlib import Path
import pytest
from utils.git_mv_detector import get_git_rename_history, should_exclude_due_to_rename

@pytest.fixture
def temp_repo():
    with tempfile.TemporaryDirectory() as td:
        repo = Path(td)
        subprocess.run(["git", "init"], cwd=repo, check=True, capture_output=True)
        subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=repo, check=True)
        subprocess.run(["git", "config", "user.name", "Test User"], cwd=repo, check=True)
        (repo / "a.py").write_text("def foo(): pass")
        subprocess.run(["git", "add", "."], cwd=repo, check=True)
        subprocess.run(["git", "commit", "-m", "initial"], cwd=repo, check=True)
        yield repo

def test_no_rename(temp_repo):
    history = get_git_rename_history(temp_repo, Path("a.py"))
    assert history == []

def test_simple_rename_same_dir(temp_repo):
    subprocess.run(["git", "mv", "a.py", "b.py"], cwd=temp_repo, check=True)
    subprocess.run(["git", "commit", "-m", "rename"], cwd=temp_repo, check=True)
    history = get_git_rename_history(temp_repo, Path("b.py"))
    assert ("a.py", "b.py") in history
    assert not should_exclude_due_to_rename("a.py", "b.py")

def test_move_to_subdir(temp_repo):
    subdir = temp_repo / "sub"
    subdir.mkdir()
    subprocess.run(["git", "mv", "a.py", "sub/a.py"], cwd=temp_repo, check=True)
    subprocess.run(["git", "commit", "-m", "move"], cwd=temp_repo, check=True)
    history = get_git_rename_history(temp_repo, Path("sub/a.py"))
    assert ("a.py", "sub/a.py") in history
    assert should_exclude_due_to_rename("a.py", "sub/a.py")

def test_move_to_different_parent(temp_repo):
    (temp_repo / "dir1").mkdir()
    (temp_repo / "dir2").mkdir()
    subprocess.run(["git", "mv", "a.py", "dir1/a.py"], cwd=temp_repo, check=True)
    subprocess.run(["git", "commit", "-m", "move1"], cwd=temp_repo, check=True)
    subprocess.run(["git", "mv", "dir1/a.py", "dir2/a.py"], cwd=temp_repo, check=True)
    subprocess.run(["git", "commit", "-m", "move2"], cwd=temp_repo, check=True)
    history = get_git_rename_history(temp_repo, Path("dir2/a.py"))
    assert ("dir1/a.py", "dir2/a.py") in history
    assert should_exclude_due_to_rename("dir1/a.py", "dir2/a.py")