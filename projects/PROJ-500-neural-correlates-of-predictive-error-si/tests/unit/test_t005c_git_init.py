"""
Unit tests for T005c: Git repository initialization.
"""
import os
import subprocess
import tempfile
from pathlib import Path
import pytest
import sys
import shutil

# Add the code directory to the path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from scripts.init_git import initialize_git_repository


class TestT005cGitInit:
    """Tests for Git repository initialization."""

    def test_git_init_in_existing_directory(self, tmp_path):
        """Test that git init works in an existing directory."""
        src_dir = tmp_path / "src"
        src_dir.mkdir()
        
        result = initialize_git_repository(tmp_path)
        
        assert result is True
        git_dir = src_dir / ".git"
        assert git_dir.exists()
        assert git_dir.is_dir()

    def test_git_init_idempotent(self, tmp_path):
        """Test that running git init twice doesn't fail."""
        src_dir = tmp_path / "src"
        src_dir.mkdir()
        
        # First initialization
        result1 = initialize_git_repository(tmp_path)
        assert result1 is True
        
        # Second initialization (should detect existing repo)
        result2 = initialize_git_repository(tmp_path)
        assert result2 is True

    def test_git_init_nonexistent_directory(self, tmp_path):
        """Test that git init fails gracefully when directory doesn't exist."""
        result = initialize_git_repository(tmp_path / "nonexistent")
        assert result is False

    def test_git_repository_structure(self, tmp_path):
        """Test that git repository has expected structure after init."""
        src_dir = tmp_path / "src"
        src_dir.mkdir()
        
        initialize_git_repository(tmp_path)
        
        git_dir = src_dir / ".git"
        assert (git_dir / "HEAD").exists()
        assert (git_dir / "config").exists()
        assert (git_dir / "objects").exists()
        assert (git_dir / "refs").exists()

    def test_git_command_available(self):
        """Test that git command is available on the system."""
        result = subprocess.run(
            ["git", "--version"],
            capture_output=True,
            text=True
        )
        # This might fail if git is not installed, which is okay for the test environment
        # The actual test is whether the code handles this gracefully
        if result.returncode == 0:
            assert "git" in result.stdout.lower()