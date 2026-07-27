"""
Integration tests for GitHub API client.
"""
import pytest
from utils.github_client import GitHubClient

@pytest.mark.skip(reason="Requires real API key and network access")
def test_github_client_fetch_repo():
    """Test fetching a real repository."""
    client = GitHubClient(api_key="test_key")
    # This would make a real API call if not skipped
    # repo = client.get_repo("octocat/Hello-World")
    # assert repo is not None
    pass
