import unittest
from unittest.mock import patch, MagicMock
import json
import os
import sys
from pathlib import Path

# Add code directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))

from fetch_data import fetch_prs_for_repo, MAX_PAGES, MAX_DURATION_SECONDS

class TestGitHubPagination(unittest.TestCase):

    def setUp(self):
        self.repo_name = "test/repo"
        self.logger = MagicMock()
        self.base_url = f"https://api.github.com/repos/{self.repo_name}/pulls"

    def create_mock_response(self, page, total_pages, has_next=True):
        """Create a mock response object mimicking GitHub API."""
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        
        # Mock data
        data = [{"number": i, "created_at": "2023-01-01T00:00:00Z", "merged_at": "2023-01-02T00:00:00Z", "labels": []} for i in range(page*100, (page+1)*100)]
        mock_resp.json.return_value = data
        
        # Mock Link header
        if has_next and page < total_pages - 1:
            mock_resp.headers = {
                'Link': f'<{self.base_url}?page={page+2}>; rel="next", <{self.base_url}?page={total_pages}>; rel="last"'
            }
        else:
            mock_resp.headers = {
                'Link': f'<{self.base_url}?page={total_pages}>; rel="last"'
            }
        
        return mock_resp

    @patch('fetch_data.api_request_with_backoff')
    def test_pagination_stops_at_max_pages(self, mock_request):
        """Test that pagination stops after MAX_PAGES (50) even if more exist."""
        total_pages = 100  # More than MAX_PAGES
        mock_request.return_value = self.create_mock_response(0, total_pages, has_next=True)
        
        # Mock subsequent calls to return empty or stop condition
        def side_effect(url, headers, logger):
            # Extract page number from URL
            if 'page=' in url:
                page = int(url.split('page=')[1].split('&')[0])
                if page > MAX_PAGES:
                    return self.create_mock_response(page, total_pages, has_next=False)
            return self.create_mock_response(0, total_pages, has_next=True)
        
        mock_request.side_effect = side_effect

        prs, pages_fetched, is_truncated = fetch_prs_for_repo(self.repo_name, self.logger)

        self.assertTrue(is_truncated, "Should be truncated because we hit MAX_PAGES")
        self.assertEqual(pages_fetched, MAX_PAGES, f"Should fetch exactly {MAX_PAGES} pages")

    @patch('fetch_data.api_request_with_backoff')
    def test_pagination_stops_at_no_next_link(self, mock_request):
        """Test that pagination stops when 'next' link is missing."""
        total_pages = 10
        mock_request.return_value = self.create_mock_response(0, total_pages, has_next=False)
        
        def side_effect(url, headers, logger):
            page = int(url.split('page=')[1].split('&')[0]) if 'page=' in url else 1
            if page >= total_pages:
                return self.create_mock_response(page, total_pages, has_next=False)
            return self.create_mock_response(page, total_pages, has_next=True)
        
        mock_request.side_effect = side_effect

        prs, pages_fetched, is_truncated = fetch_prs_for_repo(self.repo_name, self.logger)

        self.assertFalse(is_truncated, "Should not be truncated if we finish naturally")
        self.assertEqual(pages_fetched, total_pages, f"Should fetch all {total_pages} pages")

    @patch('fetch_data.api_request_with_backoff')
    def test_link_header_parsing(self, mock_request):
        """Test that Link header is correctly parsed to find next page."""
        # Simulate a response with a complex Link header
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = [{"number": 1, "created_at": "2023-01-01T00:00:00Z", "merged_at": "2023-01-02T00:00:00Z", "labels": []}]
        mock_resp.headers = {
            'Link': '<https://api.github.com/repositories/123/pulls?page=2>; rel="next", <https://api.github.com/repositories/123/pulls?page=50>; rel="last"'
        }
        
        mock_request.return_value = mock_resp
        
        # We just need to ensure the function doesn't crash and attempts to fetch next
        # The actual loop logic is tested in other methods, this verifies header access
        prs, pages_fetched, is_truncated = fetch_prs_for_repo(self.repo_name, self.logger)
        
        # Should have fetched at least one page
        self.assertGreaterEqual(pages_fetched, 1)

if __name__ == '__main__':
    unittest.main()
