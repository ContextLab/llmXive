import os
import subprocess
import pytest
from pathlib import Path
import tempfile
import shutil

# Import the function to test
from setup_remote import setup_remote

class TestSetupRemote:
    """Tests for the setup_remote function."""

    @pytest.fixture
    def temp_git_repo(self):
        """Create a temporary directory with an initialized git repo."""
        temp_dir = tempfile.mkdtemp()
        repo_path = Path(temp_dir)
        
        # Initialize git repo
        subprocess.run(["git", "init"], cwd=repo_path, check=True, capture_output=True)
        
        # Configure git user for commit (required for some git operations)
        subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=repo_path, check=True, capture_output=True)
        subprocess.run(["git", "config", "user.name", "Test User"], cwd=repo_path, check=True, capture_output=True)
        
        yield repo_path
        
        # Cleanup
        shutil.rmtree(temp_dir)

    def test_add_new_remote(self, temp_git_repo):
        """Test adding a new remote that doesn't exist yet."""
        remote_name = "origin"
        remote_url = "https://github.com/test/test-repo.git"
        
        result = setup_remote(remote_name, remote_url, temp_git_repo)
        
        assert result is True
        
        # Verify remote was added
        result = subprocess.run(
            ["git", "remote", "get-url", remote_name],
            cwd=temp_git_repo,
            capture_output=True,
            text=True
        )
        assert result.returncode == 0
        assert remote_url in result.stdout

    def test_update_existing_remote(self, temp_git_repo):
        """Test updating an existing remote with a new URL."""
        remote_name = "origin"
        initial_url = "https://github.com/old/repo.git"
        new_url = "https://github.com/new/repo.git"
        
        # Add initial remote
        subprocess.run(
            ["git", "remote", "add", remote_name, initial_url],
            cwd=temp_git_repo,
            check=True,
            capture_output=True
        )
        
        # Update the remote
        result = setup_remote(remote_name, new_url, temp_git_repo)
        
        assert result is True
        
        # Verify remote was updated
        result = subprocess.run(
            ["git", "remote", "get-url", remote_name],
            cwd=temp_git_repo,
            capture_output=True,
            text=True
        )
        assert result.returncode == 0
        assert new_url in result.stdout
        assert initial_url not in result.stdout

    def test_skip_if_same_url(self, temp_git_repo):
        """Test that the function returns True without changes if URL is already correct."""
        remote_name = "origin"
        remote_url = "https://github.com/test/test-repo.git"
        
        # Add the remote
        subprocess.run(
            ["git", "remote", "add", remote_name, remote_url],
            cwd=temp_git_repo,
            check=True,
            capture_output=True
        )
        
        # Try to add the same remote again
        result = setup_remote(remote_name, remote_url, temp_git_repo)
        
        assert result is True

    def test_git_not_available(self, temp_git_repo):
        """Test behavior when git is not available (mocked via invalid path)."""
        # This test is tricky to run in isolation, so we test the error handling
        # by attempting to use a non-existent directory
        fake_repo = Path("/nonexistent/path")
        
        with pytest.raises(RuntimeError, match="Git is not available"):
            setup_remote("origin", "https://example.com/repo.git", fake_repo)

    def test_custom_remote_name(self, temp_git_repo):
        """Test adding a remote with a custom name (not 'origin')."""
        remote_name = "upstream"
        remote_url = "https://github.com/upstream/repo.git"
        
        result = setup_remote(remote_name, remote_url, temp_git_repo)
        
        assert result is True
        
        # Verify remote was added with custom name
        result = subprocess.run(
            ["git", "remote", "get-url", remote_name],
            cwd=temp_git_repo,
            capture_output=True,
            text=True
        )
        assert result.returncode == 0
        assert remote_url in result.stdout
