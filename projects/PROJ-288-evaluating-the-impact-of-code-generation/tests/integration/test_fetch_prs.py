"""
Integration test for API fetch with mock response.
Tests the fetch_prs module using mocked GitHub API responses.
"""
import json
import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock, mock_open

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))

import requests
from data.fetch_prs import (
    RepoStats,
    load_repo_list,
    check_keywords,
    fetch_prs_for_repo,
    apply_stratified_sampling,
    apply_exclusion_logic
)
from data.rate_limiter import TokenBucketRateLimiter
from data.env_config import get_github_token


def test_load_repo_list_valid():
    """Test loading repository list from a valid file."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        f.write("microsoft/vscode,100000\ngoogle/re2,5000\n")
        temp_path = f.name

    try:
        repos = load_repo_list(temp_path)
        assert len(repos) == 2
        assert repos[0] == ("microsoft/vscode", 100000)
        assert repos[1] == ("google/re2", 5000)
    finally:
        os.unlink(temp_path)


def test_check_keywords():
    """Test keyword checking function."""
    assert check_keywords("Copilot suggestion") is True
    assert check_keywords("LLM generated code") is True
    assert check_keywords("AI generated code") is True
    assert check_keywords("Normal PR description") is False


@patch('data.fetch_prs.requests.get')
def test_fetch_prs_for_repo_with_mock(mock_get):
    """Test fetching PRs using a mocked API response."""
    # Setup mock response
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = [
        {
            "number": 123,
            "title": "Fix bug in Copilot integration",
            "body": "This PR fixes a bug related to Copilot",
            "created_at": "2023-01-01T00:00:00Z",
            "merged_at": "2023-01-02T00:00:00Z",
            "user": {"login": "testuser"},
            "additions": 50,
            "deletions": 10,
            "state": "closed"
        },
        {
            "number": 124,
            "title": "Normal feature update",
            "body": "Updated documentation",
            "created_at": "2023-01-03T00:00:00Z",
            "merged_at": None,
            "user": {"login": "anotheruser"},
            "additions": 20,
            "deletions": 5,
            "state": "open"
        }
    ]
    mock_get.return_value = mock_response

    # Create a rate limiter
    limiter = TokenBucketRateLimiter(
        rate=10,
        capacity=10,
        initial_backoff=1,
        max_backoff=60
    )

    # Fetch PRs
    prs = fetch_prs_for_repo(
        repo_id="test/repo",
        github_token="fake_token",
        rate_limiter=limiter
    )

    # Verify results
    assert len(prs) == 2
    assert prs[0]["pr_number"] == 123
    assert prs[0]["repo_id"] == "test/repo"
    assert prs[0]["origin_label"] == "Disclosing"  # Contains "Copilot"
    assert prs[1]["origin_label"] == "Non-Disclosing"


@patch('data.fetch_prs.requests.get')
def test_fetch_prs_rate_limit_handling(mock_get):
    """Test that rate limit responses are handled correctly."""
    # First call returns rate limit error
    mock_rate_limit = MagicMock()
    mock_rate_limit.status_code = 403
    mock_rate_limit.headers = {"Retry-After": "1"}
    
    # Second call returns success
    mock_success = MagicMock()
    mock_success.status_code = 200
    mock_success.json.return_value = [
        {
            "number": 456,
            "title": "Normal PR",
            "body": "No keywords here",
            "created_at": "2023-01-01T00:00:00Z",
            "merged_at": "2023-01-02T00:00:00Z",
            "user": {"login": "user"},
            "additions": 10,
            "deletions": 2,
            "state": "closed"
        }
    ]
    
    mock_get.side_effect = [mock_rate_limit, mock_success]

    limiter = TokenBucketRateLimiter(
        rate=10,
        capacity=10,
        initial_backoff=0.01,  # Fast backoff for testing
        max_backoff=0.1
    )

    prs = fetch_prs_for_repo(
        repo_id="test/repo",
        github_token="fake_token",
        rate_limiter=limiter
    )

    assert len(prs) == 1
    assert prs[0]["pr_number"] == 456


def test_apply_stratified_sampling():
    """Test stratified sampling logic."""
    # Create sample data with different star counts
    pr_data = [
        {"repo": "a", "stars": 5000, "pr_number": 1},
        {"repo": "a", "stars": 5000, "pr_number": 2},
        {"repo": "b", "stars": 50000, "pr_number": 3},
        {"repo": "b", "stars": 50000, "pr_number": 4},
        {"repo": "b", "stars": 50000, "pr_number": 5},
        {"repo": "c", "stars": 200000, "pr_number": 6},
    ]

    # Sample with 50% rate
    sampled = apply_stratified_sampling(pr_data, sample_rate=0.5, seed=42)

    # Should have approximately half the data
    assert len(sampled) <= len(pr_data)
    assert len(sampled) > 0


def test_apply_exclusion_logic():
    """Test repository exclusion logic (>50% disclosing)."""
    pr_data = [
        {"repo": "repo1", "origin_label": "Disclosing"},
        {"repo": "repo1", "origin_label": "Disclosing"},
        {"repo": "repo1", "origin_label": "Non-Disclosing"},
        {"repo": "repo2", "origin_label": "Non-Disclosing"},
        {"repo": "repo2", "origin_label": "Non-Disclosing"},
    ]

    filtered = apply_exclusion_logic(pr_data)

    # repo1 has 2/3 (66%) disclosing, should be excluded
    # repo2 has 0/2 (0%) disclosing, should be kept
    repos_in_result = set(item["repo"] for item in filtered)
    assert "repo1" not in repos_in_result
    assert "repo2" in repos_in_result


def test_repo_stats_calculation():
    """Test RepoStats dataclass."""
    stats = RepoStats(
        total_prs=100,
        disclosing_count=30,
        non_disclosing_count=70,
        disclosing_ratio=0.3
    )
    
    assert stats.total_prs == 100
    assert stats.disclosing_ratio == 0.3
    assert stats.is_excluded() == False  # 30% < 50%

    stats_high = RepoStats(
        total_prs=100,
        disclosing_count=60,
        non_disclosing_count=40,
        disclosing_ratio=0.6
    )
    assert stats_high.is_excluded() == True  # 60% > 50%

if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])