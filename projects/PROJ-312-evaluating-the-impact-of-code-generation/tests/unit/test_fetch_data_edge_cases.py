import json
import os
import unittest
from unittest.mock import patch, MagicMock
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))

from fetch_repos import fetch_repos_from_github
from utils import api_request_with_backoff


class TestFetchReposEdgeCases(unittest.TestCase):

    @patch('fetch_repos.api_request_with_backoff')
    def test_empty_response(self, mock_api_request):
        """Test handling of empty API response"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'items': []}
        mock_api_request.return_value = mock_response

        repos = fetch_repos_from_github('Python', min_stars=10000, limit=10)
        
        self.assertEqual(len(repos), 0)

    @patch('fetch_repos.api_request_with_backoff')
    def test_partial_response(self, mock_api_request):
        """Test handling of partial data in response"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'items': [
                {'full_name': 'test/repo1', 'stargazers_count': 1000, 'language': 'Python'}
            ]
        }
        mock_api_request.return_value = mock_response

        repos = fetch_repos_from_github('Python', min_stars=10000, limit=10)
        
        self.assertEqual(len(repos), 1)
        self.assertEqual(repos[0]['name'], 'test/repo1')
        self.assertEqual(repos[0]['stars'], 1000)

    @patch('fetch_repos.api_request_with_backoff')
    def test_missing_language_field(self, mock_api_request):
        """Test handling of repos without language field"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'items': [
                {'full_name': 'test/repo1', 'stargazers_count': 1000, 'language': None},
                {'full_name': 'test/repo2', 'stargazers_count': 2000}
            ]
        }
        mock_api_request.return_value = mock_response

        repos = fetch_repos_from_github('Python', min_stars=10000, limit=10)
        
        self.assertEqual(len(repos), 2)
        self.assertEqual(repos[0]['language'], 'Python')
        self.assertEqual(repos[1]['language'], 'Python')

    @patch('fetch_repos.api_request_with_backoff')
    def test_rate_limit_handling(self, mock_api_request):
        """Test that rate limit headers are logged"""
        from utils import log_api_headers
        
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.headers = {
            'X-RateLimit-Remaining': '100',
            'X-RateLimit-Reset': '1234567890',
            'X-RateLimit-Limit': '5000'
        }
        
        log_api_headers(mock_response)
        
        # Verify log file was created
        self.assertTrue(os.path.exists('logs/pipeline.log'))

    @patch('fetch_repos.requests.get')
    def test_network_timeout(self, mock_get):
        """Test handling of network timeout"""
        from requests.exceptions import Timeout
        
        mock_get.side_effect = Timeout()
        
        with self.assertRaises(Timeout):
            api_request_with_backoff('https://api.github.com/test', {}, max_retries=1)

    @patch('fetch_repos.requests.get')
    def test_http_error(self, mock_get):
        """Test handling of HTTP error"""
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.text = 'Internal Server Error'
        mock_get.return_value = mock_response
        
        with self.assertRaises(RuntimeError):
            fetch_repos_from_github('Python', min_stars=10000, limit=1)


if __name__ == '__main__':
    unittest.main()