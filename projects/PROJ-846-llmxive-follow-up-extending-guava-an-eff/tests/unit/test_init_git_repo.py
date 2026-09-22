import os
import subprocess
import tempfile
import pytest
from pathlib import Path
import sys

# Add the code directory to the path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from init_git_repo import initialize_git_repository


class TestInitializeGitRepository:
    """Test suite for git repository initialization."""

    def test_initialize_new_repository(self, tmp_path):
        """Test initializing a new git repository in an empty directory."""
        result = initialize_git_repository(str(tmp_path))
        
        assert result["status"] == "success"
        assert "initialized successfully" in result["message"].lower()
        
        # Verify .git directory exists
        git_dir = tmp_path / ".git"
        assert git_dir.exists()
        assert git_dir.is_dir()

    def test_repository_already_exists(self, tmp_path):
        """Test behavior when git repository already exists."""
        # First, initialize a repo
        initialize_git_repository(str(tmp_path))
        
        # Try to initialize again
        result = initialize_git_repository(str(tmp_path))
        
        assert result["status"] == "exists"
        assert "already initialized" in result["message"].lower()

    def test_nonexistent_directory(self):
        """Test behavior with a non-existent directory."""
        result = initialize_git_repository("/nonexistent/path/12345")
        
        assert result["status"] == "error"
        assert "does not exist" in result["message"].lower()

    def test_git_not_installed(self, monkeypatch):
        """Test behavior when git is not installed (simulated)."""
        # This test is tricky to simulate reliably, so we skip it
        # in environments where git is available
        if subprocess.run(["git", "--version"], capture_output=True).returncode == 0:
            pytest.skip("Git is installed, cannot test missing git scenario")
        
        # If we reach here, git is not installed
        with tempfile.TemporaryDirectory() as tmp_dir:
            result = initialize_git_repository(tmp_dir)
            assert result["status"] == "error"
            assert "not installed" in result["message"].lower()

    def test_default_branch_configuration(self, tmp_path):
        """Test that the default branch is configured to 'main'."""
        result = initialize_git_repository(str(tmp_path))
        
        assert result["status"] == "success"
        
        # Verify default branch is set to main
        check_result = subprocess.run(
            ["git", "config", "init.defaultBranch"],
            cwd=tmp_path,
            capture_output=True,
            text=True
        )
        
        assert check_result.stdout.strip() == "main"

    def test_returns_valid_structure(self, tmp_path):
        """Test that the return value has the expected structure."""
        result = initialize_git_repository(str(tmp_path))
        
        assert "status" in result
        assert "message" in result
        assert "output" in result
        
        assert isinstance(result["status"], str)
        assert isinstance(result["message"], str)
        assert isinstance(result["output"], str)