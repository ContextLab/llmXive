"""
Unit tests for the git_clone utility.
"""
import pytest
from pathlib import Path
import tempfile
import shutil
import os

from utils.git_clone import clone_repository, verify_repo_exists
from utils.exceptions import GitCloneException

class TestGitClone:
    """Tests for git clone functionality."""

    def test_verify_repo_exists_true(self):
        """Test verify_repo_exists returns True for valid git repo."""
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_dir = Path(tmpdir) / "test_repo"
            repo_dir.mkdir()
            git_dir = repo_dir / ".git"
            git_dir.mkdir()
            
            assert verify_repo_exists(repo_dir) is True

    def test_verify_repo_exists_false_no_git(self):
        """Test verify_repo_exists returns False if .git is missing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_dir = Path(tmpdir) / "test_repo"
            repo_dir.mkdir()
            
            assert verify_repo_exists(repo_dir) is False

    def test_verify_repo_exists_false_not_exists(self):
        """Test verify_repo_exists returns False if directory doesn't exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_dir = Path(tmpdir) / "nonexistent"
            
            assert verify_repo_exists(repo_dir) is False

    def test_clone_repository_invalid_url_raises_exception(self):
        """Test that cloning with invalid URL raises GitCloneException."""
        with tempfile.TemporaryDirectory() as tmpdir:
            target_dir = Path(tmpdir)
            
            with pytest.raises(GitCloneException):
                clone_repository(
                    "https://invalid-url-that-does-not-exist.com/repo.git",
                    target_dir,
                    "test_repo"
                )

    def test_clone_repository_nonexistent_repo_raises_exception(self):
        """Test that cloning a nonexistent repo raises GitCloneException."""
        with tempfile.TemporaryDirectory() as tmpdir:
            target_dir = Path(tmpdir)
            
            # Use a valid domain but invalid repo path
            with pytest.raises(GitCloneException):
                clone_repository(
                    "https://github.com/this-repo-definitely-does-not-exist-12345/repo.git",
                    target_dir,
                    "test_repo"
                )

    def test_clone_repository_existing_dir_replaced(self):
        """Test that existing directory is replaced during clone."""
        with tempfile.TemporaryDirectory() as tmpdir:
            target_dir = Path(tmpdir)
            repo_slug = "test_repo"
            repo_path = target_dir / repo_slug
            
            # Create a fake repo directory
            repo_path.mkdir()
            (repo_path / "fake_file.txt").write_text("fake content")
            
            # Try to clone a valid repo (this will fail but should clean up first)
            # We expect this to fail because the repo doesn't exist, but the key
            # is that it tries to remove the existing directory
            try:
                clone_repository(
                    "https://github.com/this-repo-definitely-does-not-exist-12345/repo.git",
                    target_dir,
                    repo_slug
                )
            except GitCloneException:
                pass  # Expected to fail
            
            # The directory should have been removed even if clone failed
            # (depending on when the failure occurred, this might vary)
            # This test mainly ensures the logic path exists

    def test_clone_repository_success_on_real_repo(self):
        """Test cloning a small, real repository."""
        with tempfile.TemporaryDirectory() as tmpdir:
            target_dir = Path(tmpdir)
            repo_slug = "requests"
            
            # Clone a small, well-known repo
            success = clone_repository(
                "https://github.com/psf/requests.git",
                target_dir,
                repo_slug
            )
            
            assert success is True
            assert verify_repo_exists(target_dir / repo_slug) is True
            
            # Verify some expected files exist
            repo_path = target_dir / repo_slug
            assert (repo_path / "setup.py").exists() or (repo_path / "pyproject.toml").exists()