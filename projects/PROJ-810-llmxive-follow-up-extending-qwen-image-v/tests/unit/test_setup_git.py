import os
import tempfile
from pathlib import Path
import pytest
from utils.git_utils import check_git_initialized, initialize_git_repository

class TestGitInitialization:
    def test_check_git_not_initialized(self):
        """Test that a fresh directory is not recognized as a Git repo."""
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_path = Path(tmpdir)
            assert not check_git_initialized(repo_path)

    def test_initialize_git_success(self):
        """Test successful initialization of a Git repository."""
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_path = Path(tmpdir)
            success, message = initialize_git_repository(repo_path)
            assert success
            assert (repo_path / ".git").exists()

    def test_double_initialization_idempotent(self):
        """Test that initializing twice does not raise an error."""
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_path = Path(tmpdir)
            # First init
            success1, _ = initialize_git_repository(repo_path)
            assert success1
            # Second init should detect existing repo
            success2, message = initialize_git_repository(repo_path)
            assert success2
            assert "already initialized" in message.lower()
