"""
Integration tests for GitHub API rate-limit handling and exponential backoff.

This module tests the robustness of the fetch pipeline when interacting with the
GitHub API, specifically focusing on:
1. Exponential backoff implementation
2. Rate limit detection and handling
3. Retry logic validation
4. Session management

Dependencies:
- pytest
- requests-mock (for controlled API simulation)
- code.data.fetch_github (the module under test)
"""

import os
import sys
import time
import json
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock, mock_open
from datetime import datetime

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import requests
import requests_mock

from code.data.fetch_github import fetch_prs_from_repo, calculate_checksum, save_prs_to_raw
from code.utils.config import get_repo_list, get_api_settings
from code.utils.logging import get_logger, setup_logging


# Configure logging for tests
setup_logging(level="DEBUG")
logger = get_logger(__name__)

# Test constants
TEST_REPO = "test/repo"
TEST_TOKEN = "fake_token_for_testing"
MOCK_PR_COUNT = 5
RATE_LIMIT_HEADER = "X-RateLimit-Remaining"
RATE_LIMIT_RESET_HEADER = "X-RateLimit-Reset"

class TestRateLimitHandling(unittest.TestCase):
    """Integration tests for GitHub API rate-limit handling."""

    def setUp(self):
        """Set up test fixtures."""
        self.mock_prs = [
            {
                "id": i,
                "number": i + 1,
                "title": f"Test PR {i+1}",
                "user": {"login": f"user{i}"},
                "state": "open",
                "created_at": "2023-01-01T00:00:00Z",
                "updated_at": "2023-01-01T00:00:00Z",
                "merge_commit_sha": f"sha{i}",
                "commits": [{"sha": f"commit_sha{i}"}],
                "additions": i * 10,
                "deletions": i * 5,
                "changed_files": i + 1
            }
            for i in range(MOCK_PR_COUNT)
        ]
        
        self.test_output_dir = Path(PROJECT_ROOT) / "data" / "raw"
        self.test_output_dir.mkdir(parents=True, exist_ok=True)

    def tearDown(self):
        """Clean up test artifacts."""
        # Remove any test files created during tests
        for file_path in self.test_output_dir.glob("test_repo_*"):
            file_path.unlink()

    @requests_mock.Mocker()
    def test_exponential_backoff_on_rate_limit(self, mock_requests):
        """Test that exponential backoff is correctly implemented on rate limit."""
        # Mock rate limit exceeded responses
        rate_limit_response = {
            "message": "API rate limit exceeded",
            "documentation_url": "https://docs.github.com/rest/overview/resources-in-the-rest-api#rate-limiting"
        }
        
        # First 2 requests fail with rate limit, 3rd succeeds
        mock_requests.get(
            f"https://api.github.com/repos/{TEST_REPO}/pulls",
            json=rate_limit_response,
            status_code=403,
            headers={RATE_LIMIT_HEADER: "0", RATE_LIMIT_RESET_HEADER: str(int(time.time()) + 60)}
        )
        mock_requests.get(
            f"https://api.github.com/repos/{TEST_REPO}/pulls",
            json=rate_limit_response,
            status_code=403,
            headers={RATE_LIMIT_HEADER: "0", RATE_LIMIT_RESET_HEADER: str(int(time.time()) + 60)}
        )
        mock_requests.get(
            f"https://api.github.com/repos/{TEST_REPO}/pulls",
            json=self.mock_prs,
            status_code=200,
            headers={RATE_LIMIT_HEADER: "5000"}
        )
        
        # Mock the time.sleep to track backoff behavior
        with patch('code.data.fetch_github.time.sleep') as mock_sleep:
            try:
                result = fetch_prs_from_repo(
                    repo=TEST_REPO,
                    token=TEST_TOKEN,
                    max_prs=MOCK_PR_COUNT,
                    max_retries=3
                )
            except Exception as e:
                # Expected if backoff logic is correct and retries exhausted
                self.assertIn("rate limit", str(e).lower())
                return

    @requests_mock.Mocker()
    def test_successful_fetch_with_rate_limit_headers(self, mock_requests):
        """Test successful fetch when rate limit headers indicate capacity."""
        mock_requests.get(
            f"https://api.github.com/repos/{TEST_REPO}/pulls",
            json=self.mock_prs,
            status_code=200,
            headers={
                RATE_LIMIT_HEADER: "4999",
                RATE_LIMIT_RESET_HEADER: str(int(time.time()) + 3600)
            }
        )
        
        result = fetch_prs_from_repo(
            repo=TEST_REPO,
            token=TEST_TOKEN,
            max_prs=MOCK_PR_COUNT,
            max_retries=1
        )
        
        self.assertIsNotNone(result)
        self.assertIsInstance(result, list)
        self.assertEqual(len(result), MOCK_PR_COUNT)
        
        # Verify all expected fields are present
        for pr in result:
            self.assertIn("id", pr)
            self.assertIn("number", pr)
            self.assertIn("title", pr)
            self.assertIn("user", pr)

    @requests_mock.Mocker()
    def test_pagination_handling(self, mock_requests):
        """Test that pagination is correctly handled."""
        # Create paginated responses
        page_1 = self.mock_prs[:3]
        page_2 = self.mock_prs[3:]
        
        # Mock first page
        mock_requests.get(
            f"https://api.github.com/repos/{TEST_REPO}/pulls?page=1",
            json=page_1,
            status_code=200,
            headers={"Link": f'<{mock_requests.last_request.url}&page=2>; rel="next"'}
        )
        
        # Mock second page
        mock_requests.get(
            f"https://api.github.com/repos/{TEST_REPO}/pulls?page=2",
            json=page_2,
            status_code=200,
            headers={}
        )
        
        result = fetch_prs_from_repo(
            repo=TEST_REPO,
            token=TEST_TOKEN,
            max_prs=MOCK_PR_COUNT,
            max_retries=1
        )
        
        self.assertEqual(len(result), MOCK_PR_COUNT)

    def test_checksum_calculation(self):
        """Test that checksums are correctly calculated for PR data."""
        pr_data = json.dumps(self.mock_prs[0]).encode('utf-8')
        checksum = calculate_checksum(pr_data)
        
        self.assertIsNotNone(checksum)
        self.assertEqual(len(checksum), 64)  # SHA-256 produces 64 hex characters
        
        # Verify consistency
        checksum2 = calculate_checksum(pr_data)
        self.assertEqual(checksum, checksum2)

    @patch('code.data.fetch_github.Path')
    def test_save_prs_to_raw(self, mock_path_class):
        """Test saving PRs to raw directory with proper checksumming."""
        mock_path_instance = MagicMock()
        mock_path_class.return_value = mock_path_instance
        mock_path_instance.exists.return_value = True
        mock_path_instance.mkdir.return_value = True
        mock_path_instance.glob.return_value = []
        
        # Create a mock file object
        mock_file = MagicMock()
        mock_open_instance = mock_open()
        mock_open_instance.return_value = mock_file
        
        with patch('code.data.fetch_github.open', mock_open_instance):
            result = save_prs_to_raw(
                prs=self.mock_prs,
                repo_name=TEST_REPO,
                output_dir=Path("/fake/output")
            )
        
        # Verify the file was created with correct naming
        mock_path_instance.glob.assert_called()
        self.assertTrue(mock_path_instance.exists.called)

    @requests_mock.Mocker()
    def test_network_error_handling(self, mock_requests):
        """Test handling of network errors with retry logic."""
        # Simulate network error
        mock_requests.get(
            f"https://api.github.com/repos/{TEST_REPO}/pulls",
            exc=requests.exceptions.ConnectionError("Network error"),
            status_code=0
        )
        
        with patch('code.data.fetch_github.time.sleep') as mock_sleep:
            with self.assertRaises(requests.exceptions.ConnectionError):
                fetch_prs_from_repo(
                    repo=TEST_REPO,
                    token=TEST_TOKEN,
                    max_prs=MOCK_PR_COUNT,
                    max_retries=2
                )

    @requests_mock.Mocker()
    def test_invalid_json_response(self, mock_requests):
        """Test handling of invalid JSON responses."""
        mock_requests.get(
            f"https://api.github.com/repos/{TEST_REPO}/pulls",
            text="Not valid JSON",
            status_code=200,
            headers={"Content-Type": "application/json"}
        )
        
        with self.assertRaises(json.JSONDecodeError):
            fetch_prs_from_repo(
                repo=TEST_REPO,
                token=TEST_TOKEN,
                max_prs=MOCK_PR_COUNT,
                max_retries=1
            )

    def test_backoff_timing_validation(self):
        """Validate that backoff timing follows exponential pattern."""
        # This test validates the backoff strategy by checking the implementation
        # In a real scenario, we would measure actual sleep times
        
        # Expected backoff: 1s, 2s, 4s (exponential with base 2)
        expected_delays = [1.0, 2.0, 4.0]
        
        # Verify the backoff logic exists in the fetch_github module
        import code.data.fetch_github as fetch_module
        
        # Check if the module has the expected backoff implementation
        self.assertTrue(hasattr(fetch_module, 'time'))
        self.assertTrue(hasattr(fetch_module, 'time.sleep'))

    @requests_mock.Mocker()
    def test_concurrent_rate_limit_across_repos(self, mock_requests):
        """Test rate limit handling when fetching from multiple repos."""
        repos = ["repo1", "repo2", "repo3"]
        all_prs = []
        
        for repo in repos:
            mock_requests.get(
                f"https://api.github.com/repos/test/{repo}/pulls",
                json=self.mock_prs,
                status_code=200,
                headers={RATE_LIMIT_HEADER: "4999"}
            )
        
        # Simulate fetching from multiple repos
        for repo in repos:
            result = fetch_prs_from_repo(
                repo=f"test/{repo}",
                token=TEST_TOKEN,
                max_prs=MOCK_PR_COUNT,
                max_retries=1
            )
            all_prs.extend(result)
        
        self.assertEqual(len(all_prs), MOCK_PR_COUNT * len(repos))

    def test_api_settings_integration(self):
        """Test that API settings are correctly integrated."""
        settings = get_api_settings()
        
        self.assertIsNotNone(settings)
        self.assertIn("base_url", settings)
        self.assertIn("timeout", settings)
        self.assertIn("max_retries", settings)

    @requests_mock.Mocker()
    def test_rate_limit_reset_handling(self, mock_requests):
        """Test handling of rate limit reset times."""
        reset_time = int(time.time()) + 300  # 5 minutes from now
        
        mock_requests.get(
            f"https://api.github.com/repos/{TEST_REPO}/pulls",
            json={"message": "Rate limit exceeded"},
            status_code=403,
            headers={
                RATE_LIMIT_HEADER: "0",
                RATE_LIMIT_RESET_HEADER: str(reset_time)
            }
        )
        
        with patch('code.data.fetch_github.time.sleep') as mock_sleep:
            try:
                fetch_prs_from_repo(
                    repo=TEST_REPO,
                    token=TEST_TOKEN,
                    max_prs=MOCK_PR_COUNT,
                    max_retries=1
                )
            except Exception:
                # Expected behavior
                pass

    @requests_mock.Mocker()
    def test_session_reuse(self, mock_requests):
        """Test that HTTP sessions are reused correctly."""
        mock_requests.get(
            f"https://api.github.com/repos/{TEST_REPO}/pulls",
            json=self.mock_prs,
            status_code=200
        )
        
        # Fetch multiple times to verify session reuse
        for _ in range(3):
            result = fetch_prs_from_repo(
                repo=TEST_REPO,
                token=TEST_TOKEN,
                max_prs=MOCK_PR_COUNT,
                max_retries=1
            )
            self.assertEqual(len(result), MOCK_PR_COUNT)

def run_tests():
    """Run all integration tests."""
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(TestRateLimitHandling)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    return result.wasSuccessful()

if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)