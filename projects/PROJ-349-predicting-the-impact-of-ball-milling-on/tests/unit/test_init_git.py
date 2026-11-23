"""
Unit tests for the Git repository initialization script (T004).
"""
import os
import tempfile
import shutil
from pathlib import Path
import subprocess
import pytest

from scripts.init_git_repo import main


class TestGitInitialization:
    """Test cases for git repository initialization."""

    def test_git_init_creates_dot_git_directory(self, tmp_path):
        """Test that running the script creates a .git directory."""
        # Change to temp directory
        original_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            
            # Run the main function
            result = main()
            
            # Check return code
            assert result == 0, "main() should return 0 on success"
            
            # Check that .git directory exists
            git_dir = tmp_path / ".git"
            assert git_dir.exists(), ".git directory should be created"
            assert git_dir.is_dir(), ".git should be a directory"
            
        finally:
            os.chdir(original_cwd)

    def test_git_init_idempotent(self, tmp_path):
        """Test that running the script twice doesn't cause errors."""
        original_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            
            # Run main first time
            result1 = main()
            assert result1 == 0, "First run should succeed"
            
            # Run main second time
            result2 = main()
            assert result2 == 0, "Second run should succeed (idempotent)"
            
        finally:
            os.chdir(original_cwd)

    def test_git_init_without_git_installed(self, monkeypatch):
        """Test error handling when git is not installed."""
        original_cwd = os.getcwd()
        try:
            os.chdir(tempfile.mkdtemp())
            
            # Mock subprocess.run to simulate git not found
            def mock_run(*args, **kwargs):
                raise FileNotFoundError("git command not found")
            
            monkeypatch.setattr("scripts.init_git_repo.subprocess.run", mock_run)
            
            result = main()
            assert result == 1, "Should return 1 when git is not found"
            
        finally:
            os.chdir(original_cwd)
            shutil.rmtree(os.getcwd(), ignore_errors=True)