"""
Contract test for GitHub API response parsing in code/data_acquisition/github_scraper.py.

This test verifies that the github_scraper module correctly parses GitHub API responses
into the expected PullRequest and CodeSnippet data models defined in code/utils/models.py.

It tests the parsing logic against real GitHub API response structures (mocked for stability)
to ensure contract compliance without requiring live network calls.
"""

import json
import os
from datetime import datetime
from unittest.mock import patch, MagicMock

# Import the scraper module
# Note: The path assumes this test runs from the project root
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.data_acquisition.github_scraper import parse_pr_response, parse_file_content
from code.utils.models import PullRequest, CodeSnippet
from code.utils.validators import ValidationError


def test_parse_pr_response_success():
    """
    Test successful parsing of a GitHub PR API response into a PullRequest object.
    
    Contract:
    - Input: Dict matching GitHub PullRequest API response structure
    - Output: PullRequest dataclass instance with correctly mapped fields
    - Fields: pr_id, repo_id, author_type, review_duration, file_size, complexity_score
    """
    # Mock GitHub API response structure
    mock_response = {
        "number": 1234,
        "repository_url": "https://api.github.com/repos/owner/repo",
        "user": {
            "login": "test-user",
            "type": "User"
        },
        "created_at": "2023-10-15T10:00:00Z",
        "updated_at": "2023-10-15T12:30:00Z",
        "merged_at": "2023-10-15T14:00:00Z",
        "first_comment_at": "2023-10-15T10:45:00Z",
        "state": "closed",
        "merge_commit_sha": "abc123def456",
        "additions": 50,
        "deletions": 20,
        "changed_files": 3
    }

    result = parse_pr_response(mock_response)

    # Verify type
    assert isinstance(result, PullRequest)

    # Verify field mappings
    assert result.pr_id == 1234
    assert result.repo_id == "owner/repo"
    assert result.author_type == "User"
    
    # Verify review_duration calculation (first comment to merge, or open to merge if no comment)
    # created_at: 10:00, first_comment: 10:45, merged: 14:00
    # Duration should be from first comment to merge: 3 hours 15 minutes
    expected_duration_minutes = (
        datetime(2023, 10, 15, 14, 0, 0) - 
        datetime(2023, 10, 15, 10, 45, 0)
    ).total_seconds() / 60
    assert abs(result.review_duration - expected_duration_minutes) < 1  # Allow 1 min tolerance

    # Verify file_size (total changes)
    expected_file_size = 50 + 20  # additions + deletions
    assert result.file_size == expected_file_size

    # complexity_score is typically set later by feature extraction, 
    # but should be present (defaulting to 0 or None if not calculated yet)
    assert hasattr(result, 'complexity_score')


def test_parse_pr_response_no_first_comment():
    """
    Test parsing when there is no first comment (review_duration from open to merge).
    """
    mock_response = {
        "number": 5678,
        "repository_url": "https://api.github.com/repos/owner/repo2",
        "user": {"login": "bot-user", "type": "Bot"},
        "created_at": "2023-11-01T08:00:00Z",
        "updated_at": "2023-11-01T09:00:00Z",
        "merged_at": "2023-11-01T09:30:00Z",
        "first_comment_at": None,  # No comment
        "state": "closed",
        "merge_commit_sha": "xyz789",
        "additions": 10,
        "deletions": 5,
        "changed_files": 1
    }

    result = parse_pr_response(mock_response)

    assert isinstance(result, PullRequest)
    assert result.author_type == "Bot"
    
    # Duration should be from created_at to merged_at
    expected_duration = (
        datetime(2023, 11, 1, 9, 30, 0) - 
        datetime(2023, 11, 1, 8, 0, 0)
    ).total_seconds() / 60
    assert abs(result.review_duration - expected_duration) < 1


def test_parse_pr_response_invalid_state():
    """
    Test parsing of an open PR (should still parse but state is 'open').
    """
    mock_response = {
        "number": 9999,
        "repository_url": "https://api.github.com/repos/owner/repo3",
        "user": {"login": "dev", "type": "User"},
        "created_at": "2023-12-01T10:00:00Z",
        "updated_at": "2023-12-01T10:30:00Z",
        "merged_at": None,  # Not merged yet
        "first_comment_at": None,
        "state": "open",
        "additions": 5,
        "deletions": 2,
        "changed_files": 1
    }

    result = parse_pr_response(mock_response)

    assert isinstance(result, PullRequest)
    assert result.pr_id == 9999
    # If not merged, duration might be 0 or calculated differently depending on implementation
    # The contract is that it parses without error


def test_parse_file_content_success():
    """
    Test successful parsing of GitHub file content response into CodeSnippet.
    
    Contract:
    - Input: Dict matching GitHub file content API response
    - Output: CodeSnippet dataclass instance
    - Fields: snippet_id, source_commit, generation_source, complexity_metrics, semantic_similarity_score
    """
    mock_response = {
        "sha": "commit123abc",
        "filename": "src/main.py",
        "path": "src/main.py",
        "content": "IyBDb21tZW50CnByaW50KCJIZWxsbyIp",  # Base64 encoded "print('Hello')"
        "encoding": "base64",
        "size": 18,
        "url": "https://api.github.com/repos/owner/repo/contents/src/main.py"
    }

    result = parse_file_content(mock_response)

    assert isinstance(result, CodeSnippet)
    assert result.snippet_id == "commit123abc_src/main.py"
    assert result.source_commit == "commit123abc"
    assert result.generation_source == "human"  # Default for fetched files
    assert result.complexity_metrics is not None  # Should be initialized
    assert result.semantic_similarity_score is None  # Not calculated yet


def test_parse_file_content_invalid_encoding():
    """
    Test handling of unsupported encoding (should raise ValidationError).
    """
    mock_response = {
        "sha": "commit456",
        "filename": "test.txt",
        "content": "some content",
        "encoding": "binary",  # Unsupported
        "size": 10
    }

    try:
        parse_file_content(mock_response)
        assert False, "Should have raised ValidationError"
    except ValidationError as e:
        assert "encoding" in str(e).lower()


def test_parse_pr_response_missing_fields():
    """
    Test parsing when required fields are missing (should raise ValidationError).
    """
    mock_response = {
        "number": 111,
        # Missing repository_url
        "user": {"login": "u", "type": "User"},
        "created_at": "2023-01-01T00:00:00Z"
    }

    try:
        parse_pr_response(mock_response)
        assert False, "Should have raised ValidationError"
    except ValidationError as e:
        assert "repository_url" in str(e)


if __name__ == "__main__":
    # Run tests manually if executed as script
    test_parse_pr_response_success()
    test_parse_pr_response_no_first_comment()
    test_parse_pr_response_invalid_state()
    test_parse_file_content_success()
    test_parse_file_content_invalid_encoding()
    test_parse_pr_response_missing_fields()
    print("All contract tests passed.")
