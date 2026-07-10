import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path
import sys
import os

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from code.utils.models import Repository as RepoModel
from code.utils.logging_config import get_logger

logger = get_logger(__name__)

@pytest.fixture
def mock_repo_data():
    return {
        "full_name": "test/repo",
        "stargazers_count": 10,
        "created_at": "2020-01-01T00:00:00Z",
        "updated_at": "2023-01-01T00:00:00Z",
        "clone_url": "https://github.com/test/repo.git",
        "commits_90d": 5
    }

@pytest.fixture
def temp_clone_dir(tmp_path):
    return tmp_path / "cloned_repos"

def test_filter_active_repos_stars():
    """Test that repos with <5 stars are filtered out."""
    from code import _01_data_curation as data_curation
    
    repos = [
        {"full_name": "a/a", "stargazers_count": 2},
        {"full_name": "b/b", "stargazers_count": 10}
    ]
    
    # Mock the GitHub client to avoid real API calls
    with patch.object(data_curation, 'GitHubClient') as MockClient:
        mock_instance = MagicMock()
        mock_instance.get_repository.return_value = {"stargazers_count": 10}
        mock_instance.get_commits.return_value = [1, 2] # 2 commits
        MockClient.return_value = mock_instance
        
        filtered = data_curation.filter_active_repos(repos, min_stars=5, min_commits_90d=1)
        
        assert len(filtered) == 1
        assert filtered[0]["full_name"] == "b/b"

def test_filter_active_repos_commits():
    """Test that repos with <1 commit in 90 days are filtered out."""
    from code import _01_data_curation as data_curation
    
    repos = [
        {"full_name": "a/a", "stargazers_count": 10, "commits_90d": 0},
        {"full_name": "b/b", "stargazers_count": 10, "commits_90d": 5}
    ]
    
    with patch.object(data_curation, 'GitHubClient') as MockClient:
        mock_instance = MagicMock()
        mock_instance.get_repository.return_value = {"stargazers_count": 10}
        # Simulate 0 commits for first, 5 for second
        def get_commits_side_effect(full_name, **kwargs):
            if "a/a" in full_name:
                return []
            return [1, 2, 3, 4, 5]
        
        mock_instance.get_commits.side_effect = get_commits_side_effect
        MockClient.return_value = mock_instance
        
        filtered = data_curation.filter_active_repos(repos, min_stars=5, min_commits_90d=1)
        
        assert len(filtered) == 1
        assert filtered[0]["full_name"] == "b/b"

def test_shallow_clone_repo_success(temp_clone_dir, mock_repo_data):
    """Test successful shallow clone logic (mocked)."""
    from code import _01_data_curation as data_curation
    
    mock_repo_data["full_name"] = "test/success-repo"
    
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=0)
        
        result = data_curation.shallow_clone_repo(mock_repo_data, temp_clone_dir)
        
        mock_run.assert_called_once()
        call_args = mock_run.call_args[0][0]
        assert "--depth" in call_args
        assert "100" in call_args
        assert result is not None
        assert result.exists()

def test_shallow_clone_repo_failure(temp_clone_dir, mock_repo_data):
    """Test clone failure handling."""
    from code import _01_data_curation as data_curation
    import subprocess
    
    mock_repo_data["full_name"] = "test/fail-repo"
    
    with patch("subprocess.run") as mock_run:
        mock_run.side_effect = subprocess.CalledProcessError(1, "git")
        
        result = data_curation.shallow_clone_repo(mock_repo_data, temp_clone_dir)
        
        assert result is None

def test_deduplicate_repos():
    """Test deduplication logic."""
    from code import _01_data_curation as data_curation
    
    repos = [
        {"full_name": "a/a"},
        {"full_name": "b/b"},
        {"full_name": "a/a"}
    ]
    
    unique = data_curation.deduplicate_repos(repos)
    assert len(unique) == 2
    assert unique[0]["full_name"] == "a/a"
    assert unique[1]["full_name"] == "b/b"