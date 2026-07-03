"""
Unit tests for fetch_prs.py
"""
import pytest
import json
from unittest.mock import patch, MagicMock, Mock
from pathlib import Path
import sys

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from code.src.extraction.fetch_prs import fetch_prs_for_repo, make_github_request
from code.src.extraction.schema import PullRequest

class TestFetchPRs:
    @patch('code.src.extraction.fetch_prs.make_github_request')
    def test_fetch_prs_handles_empty_response(self, mock_request):
        """Test that empty response returns empty list"""
        mock_request.return_value = None
        result = fetch_prs_for_repo("test/repo")
        assert result == []

    @patch('code.src.extraction.fetch_prs.make_github_request')
    def test_fetch_prs_handles_missing_diff(self, mock_request):
        """Test that missing diff is handled gracefully"""
        mock_data = [{
            'number': 1,
            'title': 'Test PR',
            'state': 'open',
            'created_at': '2023-01-01T00:00:00Z',
            'updated_at': '2023-01-02T00:00:00Z',
            'html_url': 'https://github.com/test/repo/pull/1',
            'user': {'login': 'testuser'},
            'comments_url': 'https://api.github.com/repos/test/repo/issues/1/comments',
            'url': 'https://api.github.com/repos/test/repo/pulls/1'
        }]
        mock_request.side_effect = [mock_data, None]  # First call PRs, second call diff fails
        
        result = fetch_prs_for_repo("test/repo")
        assert len(result) == 1
        assert result[0].diff == ""

    @patch('code.src.extraction.fetch_prs.make_github_request')
    def test_fetch_prs_handles_missing_linked_issues(self, mock_request):
        """Test that missing linked issues result in empty list"""
        mock_data = [{
            'number': 1,
            'title': 'Test PR',
            'state': 'open',
            'created_at': '2023-01-01T00:00:00Z',
            'updated_at': '2023-01-02T00:00:00Z',
            'html_url': 'https://github.com/test/repo/pull/1',
            'user': {'login': 'testuser'},
            'body': 'No issues mentioned',
            'comments_url': 'https://api.github.com/repos/test/repo/issues/1/comments',
            'url': 'https://api.github.com/repos/test/repo/pulls/1'
        }]
        mock_request.side_effect = [mock_data, []]  # PRs and empty comments
        
        result = fetch_prs_for_repo("test/repo")
        assert len(result) == 1
        assert result[0].linked_issue_ids == []

    @patch('code.src.extraction.fetch_prs.make_github_request')
    def test_fetch_prs_parses_linked_issues(self, mock_request):
        """Test that linked issues are correctly parsed from body and comments"""
        mock_pr_data = [{
            'number': 1,
            'title': 'Test PR',
            'state': 'open',
            'created_at': '2023-01-01T00:00:00Z',
            'updated_at': '2023-01-02T00:00:00Z',
            'html_url': 'https://github.com/test/repo/pull/1',
            'user': {'login': 'testuser'},
            'body': 'Fixes #123 and #456',
            'comments_url': 'https://api.github.com/repos/test/repo/issues/1/comments',
            'url': 'https://api.github.com/repos/test/repo/pulls/1'
        }]
        mock_comments_data = [
            {'body': 'Related to #789'},
            {'body': 'See #123 again'}
        ]
        mock_request.side_effect = [mock_pr_data, mock_comments_data]
        
        result = fetch_prs_for_repo("test/repo")
        assert len(result) == 1
        # Should find 123, 456, 789 (123 is duplicated but deduplicated)
        issues = sorted(result[0].linked_issue_ids)
        assert issues == [123, 456, 789]

    @patch('code.src.extraction.fetch_prs.make_github_request')
    def test_fetch_prs_creates_correct_schema(self, mock_request):
        """Test that PullRequest schema is correctly populated"""
        mock_data = [{
            'number': 99,
            'title': 'Schema Test',
            'state': 'closed',
            'created_at': '2023-05-01T12:00:00Z',
            'updated_at': '2023-05-02T12:00:00Z',
            'html_url': 'https://github.com/owner/repo/pull/99',
            'user': {'login': 'author123'},
            'body': '',
            'comments_url': 'https://api.github.com/repos/owner/repo/issues/99/comments',
            'url': 'https://api.github.com/repos/owner/repo/pulls/99'
        }]
        mock_request.side_effect = [mock_data, []]
        
        result = fetch_prs_for_repo("owner/repo")
        assert len(result) == 1
        pr = result[0]
        assert pr.pr_id == 99
        assert pr.repo == "owner/repo"
        assert pr.title == "Schema Test"
        assert pr.state == "closed"
        assert pr.author == "author123"
        assert pr.is_verified == False
        assert isinstance(pr, PullRequest)