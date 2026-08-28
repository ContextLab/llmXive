"""
Unit tests for the git_clone utility.
"""
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
import subprocess
import os
import tempfile
import shutil

from utils.git_clone import clone_repository, GitCloneException, verify_repo_exists


class TestCloneRepository:
    """Tests for the clone_repository function."""

    @patch('utils.git_clone.subprocess.run')
    @patch('utils.git_clone.Path.mkdir')
    @patch('utils.git_clone.Path.exists', return_value=False)
    def test_clone_success(self, mock_exists, mock_mkdir, mock_run, tmp_path):
        """Test successful repository clone."""
        mock_run.return_value = MagicMock(returncode=0, stderr="")
        target_dir = tmp_path / "repos"

        result = clone_repository("https://github.com/test/repo.git", target_dir)

        assert result is True
        mock_run.assert_called_once()
        args = mock_run.call_args[0][0]
        assert args[0] == 'git'
        assert args[1] == 'clone'
        assert args[2] == '--depth'
        assert args[3] == '1'

    @patch('utils.git_clone.subprocess.run')
    @patch('utils.git_clone.Path.mkdir')
    @patch('utils.git_clone.Path.exists', return_value=False)
    def test_clone_failure(self, mock_exists, mock_mkdir, mock_run, tmp_path):
        """Test repository clone failure."""
        mock_run.return_value = MagicMock(returncode=1, stderr="fatal: repository not found")
        target_dir = tmp_path / "repos"

        with pytest.raises(GitCloneException) as exc_info:
            clone_repository("https://github.com/test/repo.git", target_dir)

        assert "Failed to clone" in str(exc_info.value)

    @patch('utils.git_clone.subprocess.run')
    @patch('utils.git_clone.Path.mkdir')
    @patch('utils.git_clone.Path.exists', return_value=False)
    def test_clone_timeout(self, mock_exists, mock_mkdir, mock_run, tmp_path):
        """Test repository clone timeout."""
        mock_run.side_effect = subprocess.TimeoutExpired(cmd='git', timeout=300)
        target_dir = tmp_path / "repos"

        with pytest.raises(GitCloneException) as exc_info:
            clone_repository("https://github.com/test/repo.git", target_dir)

        assert "Timeout" in str(exc_info.value)

    @patch('utils.git_clone.subprocess.run')
    @patch('utils.git_clone.Path.mkdir')
    @patch('utils.git_clone.Path.exists', return_value=True)
    @patch('utils.git_clone.shutil.rmtree')
    def test_clone_existing_repo_removed(self, mock_rmtree, mock_exists, mock_mkdir, mock_run, tmp_path):
        """Test that existing repository is removed before cloning."""
        mock_run.return_value = MagicMock(returncode=0, stderr="")
        target_dir = tmp_path / "repos"

        clone_repository("https://github.com/test/repo.git", target_dir)

        mock_rmtree.assert_called_once()


class TestVerifyRepoExists:
    """Tests for the verify_repo_exists function."""

    def test_repo_does_not_exist(self, tmp_path):
        """Test verification when repo path doesn't exist."""
        non_existent_path = tmp_path / "non_existent"
        assert verify_repo_exists(str(non_existent_path)) is False

    def test_repo_is_file_not_dir(self, tmp_path):
        """Test verification when path is a file, not directory."""
        file_path = tmp_path / "file.txt"
        file_path.touch()
        assert verify_repo_exists(str(file_path)) is False

    def test_repo_no_python_files(self, tmp_path):
        """Test verification when repo has no Python files."""
        repo_dir = tmp_path / "repo"
        repo_dir.mkdir()
        (repo_dir / "README.md").touch()
        assert verify_repo_exists(str(repo_dir)) is False

    def test_repo_valid(self, tmp_path):
        """Test verification of a valid repository."""
        repo_dir = tmp_path / "repo"
        repo_dir.mkdir()
        (repo_dir / "main.py").touch()
        (repo_dir / "subdir").mkdir()
        (repo_dir / "subdir" / "utils.py").touch()

        assert verify_repo_exists(str(repo_dir)) is True