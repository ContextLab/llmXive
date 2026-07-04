"""
Unit tests for NpmClient.
"""
import unittest
from unittest.mock import patch, MagicMock, Mock
import requests
from src.services.npm_client import NpmClient


class TestNpmClient(unittest.TestCase):

    def setUp(self):
        self.client = NpmClient()

    @patch('src.services.npm_client.requests.Session')
    def test_get_top_packages_success(self, mock_session_class):
        """Test successful retrieval of top packages."""
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session
        
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "objects": [
                {
                    "package": {"name": "lodash"},
                    "downloads": {"downloads": 100000}
                },
                {
                    "package": {"name": "express"},
                    "downloads": {"downloads": 90000}
                }
            ]
        }
        mock_session.get.return_value = mock_response

        result = self.client.get_top_packages(size=2)

        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]["name"], "lodash")
        self.assertEqual(result[0]["weekly_downloads"], 100000)
        self.assertEqual(result[1]["name"], "express")
        
        mock_session.get.assert_called_once()

    @patch('src.services.npm_client.requests.Session')
    def test_fetch_package_metadata_success(self, mock_session_class):
        """Test successful metadata fetch."""
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session
        
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "name": "lodash",
            "version": "4.17.21",
            "time": {"created": "2011-04-18T15:30:00.000Z"}
        }
        mock_session.get.return_value = mock_response

        result = self.client.fetch_package_metadata("lodash")

        self.assertEqual(result["name"], "lodash")
        self.assertEqual(result["version"], "4.17.21")

    @patch('src.services.npm_client.requests.Session')
    def test_fetch_package_metadata_404(self, mock_session_class):
        """Test handling of 404 error."""
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session
        
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_session.get.return_value = mock_response

        result = self.client.fetch_package_metadata("non-existent-package-12345")

        self.assertIsNone(result)

    @patch('src.services.npm_client.requests.Session')
    def test_get_top_packages_empty_result(self, mock_session_class):
        """Test handling of empty result set."""
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session
        
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"objects": []}
        mock_session.get.return_value = mock_response

        result = self.client.get_top_packages(size=10)

        self.assertEqual(len(result), 0)

    def test_rate_limit_delay_calculation(self):
        """Test rate limit delay calculation logic."""
        # Mock settings to ensure predictable behavior
        self.client.settings = {"RATE_LIMIT": 10}
        delay = self.client._get_rate_limit_delay()
        self.assertEqual(delay, 6.0) # 60 / 10

        self.client.settings = {"RATE_LIMIT": 0}
        delay = self.client._get_rate_limit_delay()
        self.assertEqual(delay, 0.1) # Default fallback

if __name__ == '__main__':
    unittest.main()