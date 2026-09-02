"""
Unit tests for the git_clone utility.
"""
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
import tempfile
import shutil

from utils.exceptions import GitCloneException
from utils.git_clone import clone_repository, clone_repos_from_list, verify_repo_exists


class TestCloneRepository:
    """Tests for the clone_repository function."""

    def test_clone_repository_success(self, tmp_path):
        """Test successful cloning of a repository."""
        # This is a mock test since we can't actually clone in unit tests
        # In integration tests, we would test with a real small repo
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(returncode=0)
            
            repo_url = "https://github.com/test/repo.git"
            target_dir = tmp_path / "repos"
            
            result = clone_repository(repo_url, target_dir)
            
            assert result == target_dir / "repo"
            mock_run.assert_called_once()

    def test_clone_repository_empty_url(self, tmp_path):
        """Test that empty URL raises GitCloneException."""
        with pytest.raises(GitCloneException, match="Repository URL cannot be empty"):
            clone_repository("", tmp_path / "repos")

    def test_clone_repository_existing_repo(self, tmp_path):
        """Test that existing repos are not re-cloned."""
        repo_dir = tmp_path / "repos" / "existing_repo"
        repo_dir.mkdir(parents=True)
        (repo_dir / "test.txt").write_text("existing content")
        
        with patch('subprocess.run') as mock_run:
            result = clone_repository("https://github.com/test/repo.git", tmp_path / "repos")
            
            # Should not call git clone
            mock_run.assert_not_called()
            assert result == repo_dir

    def test_clone_repository_timeout(self, tmp_path):
        """Test timeout handling."""
        with patch('subprocess.run') as mock_run:
            mock_run.side_effect = subprocess.TimeoutExpired(cmd="git clone", timeout=300)
            
            with pytest.raises(GitCloneException, match="Timeout"):
                clone_repository("https://github.com/test/repo.git", tmp_path / "repos", timeout=300)

    def test_clone_repository_git_not_found(self, tmp_path):
        """Test handling when git is not installed."""
        with patch('subprocess.run') as mock_run:
            mock_run.side_effect = FileNotFoundError("git: command not found")
            
            with pytest.raises(GitCloneException, match="Git command not found"):
                clone_repository("https://github.com/test/repo.git", tmp_path / "repos")


class TestCloneReposFromList:
    """Tests for the clone_repos_from_list function."""

    def test_clone_repos_success(self, tmp_path):
        """Test cloning multiple repositories."""
        repo_list = [
            {"repo_url": "https://github.com/test/repo1.git"},
            {"repo_url": "https://github.com/test/repo2.git"}
        ]
        
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(returncode=0)
            
            cloned = clone_repos_from_list(repo_list, tmp_path / "repos")
            
            assert len(cloned) == 2
            assert all(p.exists() for p in cloned)

    def test_clone_repos_max_limit(self, tmp_path):
        """Test max_repos limit."""
        repo_list = [
            {"repo_url": "https://github.com/test/repo1.git"},
            {"repo_url": "https://github.com/test/repo2.git"},
            {"repo_url": "https://github.com/test/repo3.git"}
        ]
        
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(returncode=0)
            
            cloned = clone_repos_from_list(repo_list, tmp_path / "repos", max_repos=2)
            
            assert len(cloned) == 2

    def test_clone_repos_empty_list(self, tmp_path):
        """Test handling empty repository list."""
        cloned = clone_repos_from_list([], tmp_path / "repos")
        assert cloned == []

    def test_clone_repos_mixed_success_failure(self, tmp_path):
        """Test handling mixed success and failure."""
        repo_list = [
            {"repo_url": "https://github.com/test/repo1.git"},
            {"repo_url": "invalid_url"},
            {"repo_url": "https://github.com/test/repo3.git"}
        ]
        
        with patch('subprocess.run') as mock_run:
            def side_effect(*args, **kwargs):
                if "invalid_url" in str(args):
                    raise subprocess.CalledProcessError(1, "git clone", stderr="Invalid URL")
                return MagicMock(returncode=0)
            
            mock_run.side_effect = side_effect
            
            cloned = clone_repos_from_list(repo_list, tmp_path / "repos")
            
            # Should succeed for 2 repos, fail for 1
            assert len(cloned) == 2


class TestVerifyRepoExists:
    """Tests for the verify_repo_exists function."""

    def test_verify_existing_repo(self, tmp_path):
        """Test verifying an existing repository."""
        repo_dir = tmp_path / "repo"
        repo_dir.mkdir()
        (repo_dir / "test.txt").write_text("content")
        
        assert verify_repo_exists(repo_dir) is True

    def test_verify_nonexistent_repo(self, tmp_path):
        """Test verifying a non-existent repository."""
        assert verify_repo_exists(tmp_path / "nonexistent") is False

    def test_verify_empty_repo(self, tmp_path):
        """Test verifying an empty repository."""
        repo_dir = tmp_path / "empty_repo"
        repo_dir.mkdir()
        
        assert verify_repo_exists(repo_dir) is False

    def test_verify_file_instead_of_dir(self, tmp_path):
        """Test verifying a file instead of directory."""
        file_path = tmp_path / "file.txt"
        file_path.write_text("content")
        
        assert verify_repo_exists(file_path) is False