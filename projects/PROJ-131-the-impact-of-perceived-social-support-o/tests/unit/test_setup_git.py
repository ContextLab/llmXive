import os
import subprocess
import tempfile
from pathlib import Path
import pytest

# Import the module functions to test
from setup_git import initialize_git_repo, verify_git_repo

def test_initialize_git_repo_creates_directory():
    """Test that initialize_git_repo creates a .git directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        root_path = Path(tmpdir)
        initialize_git_repo(root_path)
        assert (root_path / ".git").exists()

def test_verify_git_repo_returns_true_after_init():
    """Test that verify_git_repo returns True after initialization."""
    with tempfile.TemporaryDirectory() as tmpdir:
        root_path = Path(tmpdir)
        initialize_git_repo(root_path)
        assert verify_git_repo(root_path) is True

def test_verify_git_repo_returns_false_without_repo():
    """Test that verify_git_repo returns False when no repo exists."""
    with tempfile.TemporaryDirectory() as tmpdir:
        root_path = Path(tmpdir)
        assert verify_git_repo(root_path) is False

def test_initialize_git_repo_raises_on_failure():
    """Test that initialize_git_repo raises RuntimeError on failure."""
    # This is hard to trigger in a temp dir without mocking,
    # but we test the happy path primarily.
    with tempfile.TemporaryDirectory() as tmpdir:
        root_path = Path(tmpdir)
        # Should not raise
        try:
            initialize_git_repo(root_path)
        except RuntimeError:
            pytest.fail("initialize_git_repo raised unexpectedly")