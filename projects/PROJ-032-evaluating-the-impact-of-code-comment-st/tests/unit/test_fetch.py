import pytest
import os
import subprocess
from unittest.mock import patch, MagicMock
from pathlib import Path
import shutil
import tempfile

# Import the function to test
# Assuming fetch.py is in the code directory and utils is accessible
import sys
sys.path.insert(0, 'code')
from fetch import has_valid_git_history, clone_batch

class TestHasValidGitHistory:
    def setup_method(self):
        # Create a temporary directory for testing
        self.temp_dir = tempfile.mkdtemp()
        self.repo_path = Path(self.temp_dir) / "test_repo"
        self.repo_path.mkdir()
        
        # Initialize a valid git repo with one commit
        subprocess.run(["git", "init"], cwd=self.repo_path, check=True, capture_output=True)
        (self.repo_path / "test.txt").write_text("content")
        subprocess.run(["git", "add", "."], cwd=self.repo_path, check=True, capture_output=True)
        subprocess.run(["git", "-c", "user.name=test", "-c", "user.email=test@test.com", "commit", "-m", "initial"], 
                       cwd=self.repo_path, check=True, capture_output=True)

    def teardown_method(self):
        # Cleanup
        shutil.rmtree(self.temp_dir)

    def test_valid_history(self):
        assert has_valid_git_history(self.repo_path) is True

    def test_empty_history(self):
        # Create a new repo without commits
        empty_repo = Path(self.temp_dir) / "empty_repo"
        empty_repo.mkdir()
        subprocess.run(["git", "init"], cwd=empty_repo, check=True, capture_output=True)
        
        assert has_valid_git_history(empty_repo) is False

    def test_non_git_directory(self):
        non_git = Path(self.temp_dir) / "not_git"
        non_git.mkdir()
        
        assert has_valid_git_history(non_git) is False

    def test_missing_directory(self):
        missing = Path(self.temp_dir) / "missing"
        
        assert has_valid_git_history(missing) is False

class TestCloneBatch:
    def setup_method(self):
        self.temp_dir = tempfile.mkdtemp()
        self.target_dir = Path(self.temp_dir) / "clones"
        self.target_dir.mkdir()

    def teardown_method(self):
        shutil.rmtree(self.temp_dir)

    @patch('fetch.subprocess.run')
    @patch('fetch.has_valid_git_history')
    def test_clone_success_and_history_check(self, mock_history, mock_run):
        # Mock successful clone
        mock_run.return_value = MagicMock(returncode=0)
        mock_history.return_value = True
        
        candidates = ["test/repo1"]
        result = clone_batch(candidates, self.target_dir, max_concurrent=1)
        
        assert len(result) == 1
        assert mock_history.called
        
    @patch('fetch.subprocess.run')
    @patch('fetch.has_valid_git_history')
    def test_clone_excludes_empty_history(self, mock_history, mock_run):
        # Mock successful clone
        mock_run.return_value = MagicMock(returncode=0)
        # But history check fails
        mock_history.return_value = False
        
        candidates = ["test/repo1"]
        result = clone_batch(candidates, self.target_dir, max_concurrent=1)
        
        # Should be empty because history check failed
        assert len(result) == 0
        assert mock_history.called

    @patch('fetch.subprocess.run')
    def test_clone_retry_logic(self, mock_run):
        # First two attempts fail, third succeeds
        mock_run.side_effect = [
            subprocess.CalledProcessError(1, "git"),
            subprocess.CalledProcessError(1, "git"),
            MagicMock(returncode=0)
        ]
        
        candidates = ["test/repo1"]
        result = clone_batch(candidates, self.target_dir, max_concurrent=1)
        
        # Should succeed on 3rd attempt
        assert len(result) == 1
        assert mock_run.call_count == 3
        
    @patch('fetch.subprocess.run')
    def test_clone_fails_after_max_retries(self, mock_run):
        # Always fail
        mock_run.side_effect = subprocess.CalledProcessError(1, "git")
        
        candidates = ["test/repo1"]
        result = clone_batch(candidates, self.target_dir, max_concurrent=1)
        
        # Should fail after 3 retries
        assert len(result) == 0
        assert mock_run.call_count == 3