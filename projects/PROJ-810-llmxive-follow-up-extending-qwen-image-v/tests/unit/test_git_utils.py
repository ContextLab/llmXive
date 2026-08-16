"""
Unit tests for git utility functions.
"""
import os
import tempfile
from pathlib import Path
import pytest

from utils.git_utils import (
    check_git_initialized,
    initialize_git_repository
)


class TestGitUtils:
    """Test cases for git utility functions."""

    def test_check_git_initialized_false(self):
        """Test that check_git_initialized returns False for non-git directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_path = Path(tmpdir)
            assert not check_git_initialized(repo_path)

    def test_check_git_initialized_true(self):
        """Test that check_git_initialized returns True for git directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_path = Path(tmpdir)
            # Initialize git repo
            initialize_git_repository(repo_path)
            assert check_git_initialized(repo_path)

    def test_initialize_git_repository_success(self):
        """Test successful git repository initialization."""
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_path = Path(tmpdir)
            success, message = initialize_git_repository(repo_path)

            assert success is True
            assert "initialized" in message.lower()
            assert check_git_initialized(repo_path)

    def test_initialize_git_repository_already_exists(self):
        """Test that initializing existing repo returns success."""
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_path = Path(tmpdir)
            # First initialization
            initialize_git_repository(repo_path)
            # Second initialization (should succeed)
            success, message = initialize_git_repository(repo_path)

            assert success is True
            assert "already initialized" in message.lower()

    def test_initialize_git_repository_creates_git_dir(self):
        """Test that initialization creates .git directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_path = Path(tmpdir)
            initialize_git_repository(repo_path)

            git_dir = repo_path / ".git"
            assert git_dir.exists()
            assert git_dir.is_dir()
