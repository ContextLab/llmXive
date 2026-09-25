import os
import subprocess
import tempfile
import shutil
from pathlib import Path
import pytest

# Import the functions we want to test
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))
from setup_git import initialize_git_repo, verify_git_repo

class TestGitSetup:
    """Test cases for git repository initialization and verification."""

    def test_initialize_new_repo(self, tmp_path):
        """Test that a new git repository can be initialized."""
        assert not (tmp_path / ".git").exists()
        result = initialize_git_repo(tmp_path)
        assert result is True
        assert (tmp_path / ".git").exists()

    def test_verify_existing_repo(self, tmp_path):
        """Test that an existing git repository can be verified."""
        # First initialize
        initialize_git_repo(tmp_path)
        
        # Then verify
        result = verify_git_repo(tmp_path)
        assert result is True

    def test_verify_nonexistent_repo(self, tmp_path):
        """Test verification fails when repo doesn't exist."""
        result = verify_git_repo(tmp_path)
        assert result is False

    def test_double_initialization(self, tmp_path):
        """Test that initializing twice doesn't cause errors."""
        # First initialization
        result1 = initialize_git_repo(tmp_path)
        assert result1 is True
        
        # Second initialization (should detect existing repo)
        result2 = initialize_git_repo(tmp_path)
        assert result2 is True

    def test_git_status_after_init(self, tmp_path):
        """Test that git status works after initialization."""
        initialize_git_repo(tmp_path)
        
        result = subprocess.run(
            ["git", "status"],
            cwd=tmp_path,
            capture_output=True,
            text=True
        )
        
        assert result.returncode == 0
        assert "On branch" in result.stdout or "HEAD" in result.stdout