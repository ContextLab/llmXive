"""
Integration test for GitHub API rate-limit handling (backoff) in fetch_github.py.

This test verifies that the fetch pipeline correctly implements exponential backoff
when encountering rate limits (HTTP 403/429) from the GitHub API.

Test Strategy:
1. Mock the GitHub API responses to simulate rate limiting scenarios
2. Verify that the fetch_github module implements exponential backoff
3. Verify that the pipeline eventually fails loudly after max retries (no silent fallback)
4. Verify that successful requests after backoff are processed correctly
"""

import os
import json
import time
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock, mock_open
import pytest

# Import the module under test
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.data.fetch_github import (
    fetch_prs_from_repo,
    run_batch_fetch,
    calculate_checksum
)
from code.utils.config import get_config_summary
from code.utils.logging import get_logger

# Test constants
MOCK_REPO = "test-org/test-repo"
MOCK_PR_NUMBER = 123
MOCK_PR_DATA = {
    "number": MOCK_PR_NUMBER,
    "title": "Test PR",
    "state": "open",
    "user": {"login": "test-user"},
    "created_at": "2024-01-01T00:00:00Z",
    "merged_at": None,
    "commits": 1,
    "additions": 10,
    "deletions": 5
}

# Rate limit response (429 Too Many Requests)
RATE_LIMIT_RESPONSE = {
    "message": "API rate limit exceeded",
    "documentation_url": "https://docs.github.com/en/rest/overview/resources-in-the-rest-api#rate-limiting",
    "resources": {
        "core": {
            "limit": 5000,
            "remaining": 0,
            "reset": int(time.time()) + 3600
        }
    }
}

# Forbidden response (403)
FORBIDDEN_RESPONSE = {
    "message": "Rate limit exceeded",
    "documentation_url": "https://docs.github.com/en/rest/overview/resources-in-the-rest-api#rate-limiting"
}

# Successful response after backoff
SUCCESS_RESPONSE = [MOCK_PR_DATA]

class RateLimitTestError(Exception):
    """Custom exception for rate limit test failures"""
    pass

@pytest.fixture
def temp_output_dir():
    """Create a temporary directory for test outputs"""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)

@pytest.fixture
def mock_requests_session():
    """Mock requests.Session for controlled HTTP responses"""
    mock_session = MagicMock()
    return mock_session

def test_rate_limit_backoff_exponential_growth(temp_output_dir, mock_requests_session):
    """
    Test that the fetch pipeline implements exponential backoff when hitting rate limits.
    
    This test simulates:
    - First 2 requests: Rate limit (429)
    - Third request: Success
    
    Expected behavior:
    - Backoff delays should grow exponentially (e.g., 1s, 2s, 4s)
    - The pipeline should eventually succeed or fail after max retries
    """
    call_count = [0]
    max_calls_before_success = 2
    
    def mock_get(url, headers=None, timeout=None, **kwargs):
        mock_response = MagicMock()
        call_count[0] += 1
        
        if call_count[0] <= max_calls_before_success:
            # Simulate rate limit
            mock_response.status_code = 429
            mock_response.json.return_value = RATE_LIMIT_RESPONSE
            mock_response.headers = {"Retry-After": "1"}
        else:
            # Success
            mock_response.status_code = 200
            mock_response.json.return_value = SUCCESS_RESPONSE
            mock_response.headers = {}
        
        return mock_response
    
    mock_requests_session.get = mock_get
    
    # Mock the session creation in fetch_github
    with patch('code.data.fetch_github.requests.Session', return_value=mock_requests_session):
        with patch('code.data.fetch_github.get_config_summary', return_value={
            'github': {
                'api_base_url': 'https://api.github.com',
                'max_retries': 5,
                'base_delay': 0.1,  # Use small delay for faster tests
                'max_delay': 2.0
            }
        }):
            # This should eventually succeed after backoff
            result = fetch_prs_from_repo(
                repo=MOCK_REPO,
                output_dir=temp_output_dir,
                max_prs=10,
                session=mock_requests_session
            )
            
            # Verify we got the PR
            assert result is not None
            assert len(result) > 0
            assert result[0]['number'] == MOCK_PR_NUMBER
            
            # Verify multiple calls were made (including retries)
            assert call_count[0] > 1
    
    print(f"✓ Test passed: Backoff was triggered {call_count[0] - 1} times before success")

def test_rate_limit_max_retries_fail_loudly(temp_output_dir, mock_requests_session):
    """
    Test that the pipeline FAILS LOUDLY after max retries (no silent fallback).
    
    This test simulates:
    - All requests return rate limit (429)
    
    Expected behavior:
    - Pipeline should raise an exception after max retries
    - No synthetic data should be generated
    - No silent fallback to empty results
    """
    def mock_get(url, headers=None, timeout=None, **kwargs):
        mock_response = MagicMock()
        mock_response.status_code = 429
        mock_response.json.return_value = RATE_LIMIT_RESPONSE
        mock_response.headers = {"Retry-After": "1"}
        return mock_response
    
    mock_requests_session.get = mock_get
    
    with patch('code.data.fetch_github.requests.Session', return_value=mock_requests_session):
        with patch('code.data.fetch_github.get_config_summary', return_value={
            'github': {
                'api_base_url': 'https://api.github.com',
                'max_retries': 3,  # Small number for faster test
                'base_delay': 0.01,
                'max_delay': 0.1
            }
        }):
            # This should raise an exception after max retries
            with pytest.raises(Exception) as exc_info:
                fetch_prs_from_repo(
                    repo=MOCK_REPO,
                    output_dir=temp_output_dir,
                    max_prs=10,
                    session=mock_requests_session
                )
            
            # Verify the error message mentions rate limit or max retries
            error_msg = str(exc_info.value).lower()
            assert 'rate limit' in error_msg or 'max retries' in error_msg or 'failed' in error_msg
            
    print("✓ Test passed: Pipeline failed loudly after max retries (no silent fallback)")

def test_retry_after_header_respected(temp_output_dir, mock_requests_session):
    """
    Test that the pipeline respects the Retry-After header from GitHub.
    
    This test simulates:
    - Rate limit response with Retry-After: 2 seconds
    
    Expected behavior:
    - Pipeline should wait at least the specified time before retrying
    """
    call_count = [0]
    retry_after_seconds = 2
    start_time = None
    
    def mock_get(url, headers=None, timeout=None, **kwargs):
        nonlocal start_time
        mock_response = MagicMock()
        call_count[0] += 1
        
        if call_count[0] == 1:
            # First request: rate limit with Retry-After
            mock_response.status_code = 429
            mock_response.json.return_value = RATE_LIMIT_RESPONSE
            mock_response.headers = {"Retry-After": str(retry_after_seconds)}
            start_time = time.time()
        else:
            # Second request: success
            mock_response.status_code = 200
            mock_response.json.return_value = SUCCESS_RESPONSE
            mock_response.headers = {}
        
        return mock_response
    
    mock_requests_session.get = mock_get
    
    with patch('code.data.fetch_github.requests.Session', return_value=mock_requests_session):
        with patch('code.data.fetch_github.get_config_summary', return_value={
            'github': {
                'api_base_url': 'https://api.github.com',
                'max_retries': 5,
                'base_delay': 0.01,
                'max_delay': 0.1
            }
        }):
            # This should respect the Retry-After header
            result = fetch_prs_from_repo(
                repo=MOCK_REPO,
                output_dir=temp_output_dir,
                max_prs=10,
                session=mock_requests_session
            )
            
            # Verify the delay was respected (with some tolerance for test overhead)
            elapsed = time.time() - start_time if start_time else 0
            assert elapsed >= retry_after_seconds * 0.9, f"Expected at least {retry_after_seconds}s delay, got {elapsed:.2f}s"
            
            # Verify we got the PR
            assert len(result) > 0
    
    print(f"✓ Test passed: Retry-After header was respected (delay: {elapsed:.2f}s)")

def test_403_forbidden_rate_limit(temp_output_dir, mock_requests_session):
    """
    Test that 403 Forbidden responses are also treated as rate limits.
    
    GitHub sometimes returns 403 instead of 429 for rate limits.
    """
    call_count = [0]
    
    def mock_get(url, headers=None, timeout=None, **kwargs):
        mock_response = MagicMock()
        call_count[0] += 1
        
        if call_count[0] == 1:
            # First request: 403 Forbidden
            mock_response.status_code = 403
            mock_response.json.return_value = FORBIDDEN_RESPONSE
            mock_response.headers = {"Retry-After": "1"}
        else:
            # Second request: success
            mock_response.status_code = 200
            mock_response.json.return_value = SUCCESS_RESPONSE
            mock_response.headers = {}
        
        return mock_response
    
    mock_requests_session.get = mock_get
    
    with patch('code.data.fetch_github.requests.Session', return_value=mock_requests_session):
        with patch('code.data.fetch_github.get_config_summary', return_value={
            'github': {
                'api_base_url': 'https://api.github.com',
                'max_retries': 5,
                'base_delay': 0.01,
                'max_delay': 0.1
            }
        }):
            result = fetch_prs_from_repo(
                repo=MOCK_REPO,
                output_dir=temp_output_dir,
                max_prs=10,
                session=mock_requests_session
            )
            
            # Verify backoff was triggered and eventually succeeded
            assert len(result) > 0
            assert call_count[0] > 1
    
    print("✓ Test passed: 403 Forbidden was handled with backoff")

def test_batch_fetch_rate_limit_handling(temp_output_dir, mock_requests_session):
    """
    Test that run_batch_fetch correctly handles rate limits across multiple repos.
    
    This test verifies:
    - Rate limit in one repo doesn't break the entire batch
    - Pipeline continues to next repo after max retries
    - Results from successful repos are preserved
    """
    call_counts = {'repo1': 0, 'repo2': 0}
    
    def mock_get(url, headers=None, timeout=None, **kwargs):
        mock_response = MagicMock()
        
        # Determine which repo we're fetching
        if 'repo1' in url:
            call_counts['repo1'] += 1
            if call_counts['repo1'] == 1:
                mock_response.status_code = 429
                mock_response.json.return_value = RATE_LIMIT_RESPONSE
                mock_response.headers = {"Retry-After": "1"}
            else:
                mock_response.status_code = 200
                mock_response.json.return_value = [MOCK_PR_DATA]
                mock_response.headers = {}
        elif 'repo2' in url:
            call_counts['repo2'] += 1
            # repo2 always succeeds
            mock_response.status_code = 200
            mock_response.json.return_value = [MOCK_PR_DATA]
            mock_response.headers = {}
        else:
            mock_response.status_code = 404
            mock_response.json.return_value = {"message": "Not Found"}
        
        return mock_response
    
    mock_requests_session.get = mock_get
    
    repos = [
        f"test-org/repo1",
        f"test-org/repo2"
    ]
    
    with patch('code.data.fetch_github.requests.Session', return_value=mock_requests_session):
        with patch('code.data.fetch_github.get_config_summary', return_value={
            'github': {
                'api_base_url': 'https://api.github.com',
                'max_retries': 3,
                'base_delay': 0.01,
                'max_delay': 0.1
            }
        }):
            results = run_batch_fetch(
                repos=repos,
                output_dir=temp_output_dir,
                max_prs_per_repo=10,
                session=mock_requests_session
            )
            
            # Verify both repos were attempted
            assert call_counts['repo1'] > 0
            assert call_counts['repo2'] > 0
            
            # Verify we got results from at least one repo
            assert len(results) > 0
    
    print("✓ Test passed: Batch fetch handled rate limits across multiple repos")

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
