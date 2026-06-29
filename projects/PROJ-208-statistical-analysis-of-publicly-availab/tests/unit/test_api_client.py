"""Unit tests for GitHub API client."""

import time
from unittest.mock import Mock, patch, MagicMock
import pytest
from utils.api_client import GitHubAPIClient, fetch_issues_for_repositories


class TestGitHubAPIClient:
    """Tests for GitHubAPIClient class."""
    
    def test_init_with_token(self):
        """Test client initialization with token."""
        client = GitHubAPIClient(token="test_token")
        assert client.token == "test_token"
        assert client.base_url == "https://api.github.com"
    
    def test_init_without_token(self):
        """Test client initialization without token."""
        client = GitHubAPIClient()
        assert client.token is None
        assert client.rate_limit_remaining == 60
    
    def test_get_rate_limit_info(self):
        """Test rate limit info retrieval."""
        client = GitHubAPIClient()
        
        with patch.object(client, '_get_rate_limit') as mock_limit:
            mock_limit.return_value = {
                "core": {
                    "remaining": 5000,
                    "limit": 5000,
                    "reset": int(time.time()) + 3600,
                    "used": 0
                }
            }
            
            info = client.get_rate_limit_info()
            assert info["remaining"] == 5000
            assert info["limit"] == 5000
            assert "reset" in info
    
    @patch('utils.api_client.GitHubAPIClient._make_request')
    def test_fetch_issues_basic(self, mock_request):
        """Test basic issue fetching."""
        client = GitHubAPIClient()
        
        mock_response = [{
            "number": 1,
            "title": "Test Issue",
            "state": "closed",
            "created_at": "2024-01-01T00:00:00Z",
            "updated_at": "2024-01-02T00:00:00Z",
            "closed_at": "2024-01-02T00:00:00Z",
            "user": {"login": "testuser"},
            "labels": [{"name": "bug"}]
        }]
        
        mock_request.return_value = mock_response
        
        issues = client.fetch_issues("owner", "repo", state="closed", per_page=100)
        
        assert len(issues) == 1
        assert issues[0]["issue_number"] == 1
        assert issues[0]["title"] == "Test Issue"
        assert issues[0]["state"] == "closed"
    
    @patch('utils.api_client.GitHubAPIClient._make_request')
    def test_fetch_issues_excludes_pull_requests(self, mock_request):
        """Test that pull requests are excluded from issues."""
        client = GitHubAPIClient()
        
        mock_response = [
            {
                "number": 1,
                "title": "Regular Issue",
                "state": "closed",
                "created_at": "2024-01-01T00:00:00Z",
                "updated_at": "2024-01-02T00:00:00Z",
                "closed_at": "2024-01-02T00:00:00Z",
                "user": {"login": "testuser"},
                "labels": []
            },
            {
                "number": 2,
                "title": "Pull Request",
                "state": "closed",
                "created_at": "2024-01-01T00:00:00Z",
                "updated_at": "2024-01-02T00:00:00Z",
                "closed_at": "2024-01-02T00:00:00Z",
                "user": {"login": "testuser"},
                "labels": [],
                "pull_request": {"url": "https://api.github.com/pulls/2"}
            }
        ]
        
        mock_request.return_value = mock_response
        
        issues = client.fetch_issues("owner", "repo", state="closed")
        
        assert len(issues) == 1
        assert issues[0]["issue_number"] == 1
    
    @patch('utils.api_client.GitHubAPIClient._make_request')
    def test_fetch_issues_pagination(self, mock_request):
        """Test pagination in issue fetching."""
        client = GitHubAPIClient()
        
        # First page returns max items, second page returns fewer
        page1 = [{"number": i, "title": f"Issue {i}", "state": "closed",
                 "created_at": "2024-01-01T00:00:00Z", "updated_at": "2024-01-02T00:00:00Z",
                 "closed_at": "2024-01-02T00:00:00Z", "user": {"login": "test"}, "labels": []}
                for i in range(1, 101)]
        page2 = [{"number": i, "title": f"Issue {i}", "state": "closed",
                 "created_at": "2024-01-01T00:00:00Z", "updated_at": "2024-01-02T00:00:00Z",
                 "closed_at": "2024-01-02T00:00:00Z", "user": {"login": "test"}, "labels": []}
                for i in range(101, 151)]
        
        call_count = [0]
        
        def side_effect(url, params=None):
            call_count[0] += 1
            if call_count[0] == 1:
                return page1
            else:
                return page2[:0]  # Empty to stop pagination
        
        mock_request.side_effect = side_effect
        
        issues = client.fetch_issues("owner", "repo", state="closed", per_page=100)
        
        assert len(issues) == 100
        assert call_count[0] == 2
    
    def test_max_issues_limit(self):
        """Test that max_issues parameter limits results."""
        client = GitHubAPIClient()
        
        with patch.object(client, 'fetch_issues') as mock_fetch:
            mock_fetch.return_value = [{"issue_number": i} for i in range(200)]
            
            issues = client.fetch_issues("owner", "repo", max_issues=50)
            
            assert len(issues) == 50
    
    def test_fetch_issues_for_repositories(self):
        """Test fetching issues across multiple repositories."""
        repos = [
            {"owner": "repo1", "repo": "test1"},
            {"owner": "repo2", "repo": "test2"}
        ]
        
        with patch('utils.api_client.GitHubAPIClient') as mock_client_class:
            mock_client = Mock()
            mock_client.fetch_issues.side_effect = [
                [{"issue_number": 1, "owner": "repo1", "repo": "test1"}],
                [{"issue_number": 2, "owner": "repo2", "repo": "test2"}]
            ]
            mock_client_class.return_value = mock_client
            
            issues = fetch_issues_for_repositories(repos)
            
            assert len(issues) == 2
            assert mock_client.fetch_issues.call_count == 2


class TestRateLimitHandling:
    """Tests for rate limit handling."""
    
    def test_rate_limit_remaining_updates(self):
        """Test that rate limit remaining is updated."""
        client = GitHubAPIClient()
        client.rate_limit_remaining = 100
        
        with patch.object(client, '_get_rate_limit') as mock_limit:
            mock_limit.return_value = {
                "core": {
                    "remaining": 50,
                    "limit": 5000,
                    "reset": int(time.time()) + 3600,
                    "used": 4950
                }
            }
            
            client._check_rate_limit()
            
            assert client.rate_limit_remaining == 50
    
    def test_rate_limit_zero_triggers_wait(self):
        """Test that zero rate limit triggers wait logic."""
        client = GitHubAPIClient()
        
        with patch.object(client, '_get_rate_limit') as mock_limit:
            with patch('utils.api_client.time.sleep') as mock_sleep:
                mock_limit.return_value = {
                    "core": {
                        "remaining": 0,
                        "limit": 60,
                        "reset": int(time.time()) + 60,
                        "used": 60
                    }
                }
                
                client._check_rate_limit()
                
                mock_sleep.assert_called()
                
                # Verify rate limit was updated after wait
                assert mock_limit.call_count == 2
