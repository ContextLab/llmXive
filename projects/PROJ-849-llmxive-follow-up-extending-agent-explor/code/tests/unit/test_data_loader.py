"""
Unit tests for data loader.
"""
import pytest
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock
from lib.data_loader import check_url_reachability, DataLoaderError

class TestDataLoader:
    @patch('lib.data_loader.requests.head')
    def test_check_url_reachability_success(self, mock_head):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_head.return_value = mock_response
        assert check_url_reachability("http://example.com") is True

    @patch('lib.data_loader.requests.head')
    def test_check_url_reachability_fail(self, mock_head):
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_head.return_value = mock_response
        assert check_url_reachability("http://example.com") is False

    @patch('lib.data_loader.requests.head')
    def test_check_url_reachability_exception(self, mock_head):
        mock_head.side_effect = Exception("Network error")
        assert check_url_reachability("http://example.com") is False
