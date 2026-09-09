"""
Unit tests for the Git initialization script (T005c).
"""
import os
import subprocess
import tempfile
from pathlib import Path
import pytest

# Import the function to test
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))
from scripts.init_git import initialize_git_repository


class TestT005cGitInit:
    """Test cases for Git repository initialization."""

    def test_git_init_success(self, tmp_path):
        """Test that git init succeeds in a valid directory."""
        result = initialize_git_repository(tmp_path)
        assert result is True
        # Verify .git directory was created
        git_dir = tmp_path / ".git"
        assert git_dir.exists()
        assert git_dir.is_dir()

    def test_git_init_nonexistent_directory(self, tmp_path):
        """Test that git init fails for a non-existent directory."""
        nonexistent = tmp_path / "nonexistent"
        result = initialize_git_repository(nonexistent)
        assert result is False

    def test_git_init_creates_gitignore(self, tmp_path):
        """Test that git init creates the .git directory structure."""
        result = initialize_git_repository(tmp_path)
        assert result is True

        # Check for basic .git structure
        git_dir = tmp_path / ".git"
        assert (git_dir / "HEAD").exists()
        assert (git_dir / "config").exists()
        assert (git_dir / "objects").exists()
        assert (git_dir / "refs").exists()

    def test_git_init_idempotent(self, tmp_path):
        """Test that running git init twice doesn't fail."""
        # First init
        result1 = initialize_git_repository(tmp_path)
        assert result1 is True

        # Second init (should not fail)
        result2 = initialize_git_repository(tmp_path)
        assert result2 is True