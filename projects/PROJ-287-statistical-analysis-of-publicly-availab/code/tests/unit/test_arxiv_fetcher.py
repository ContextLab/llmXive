"""
Unit tests for the ArXiv Fetcher.

Tests cover:
- Year filtering logic.
- Retry logic (mocked).
- XML parsing logic (mocked).
"""

import unittest
from unittest.mock import patch, MagicMock
import xml.etree.ElementTree as ET
import time
import sys
import os

# Add parent to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from src.data.fetch.arxiv_fetcher import (
    _parse_arxiv_date,
    _is_valid_year,
    _calculate_backoff,
    _parse_arxiv_entry,
    fetch_arxiv_abstracts
)
from src.models.entities import AbstractRecord

class TestArxivFetcherLogic(unittest.TestCase):
    
    def test_parse_arxiv_date_valid(self):
        """Test parsing valid ISO 8601 dates."""
        self.assertEqual(_parse_arxiv_date("2023-01-15T12:00:00Z"), 2023)
        self.assertEqual(_parse_arxiv_date("2000-05-20T08:30:00Z"), 2000)
        self.assertEqual(_parse_arxiv_date("2024-12-31T23:59:59Z"), 2024)

    def test_parse_arxiv_date_invalid(self):
        """Test parsing invalid dates."""
        self.assertIsNone(_parse_arxiv_date(""))
        self.assertIsNone(_parse_arxiv_date("invalid"))
        self.assertIsNone(_parse_arxiv_date(None))

    def test_is_valid_year(self):
        """Test year filtering logic."""
        # Valid range
        self.assertTrue(_is_valid_year(2000))
        self.assertTrue(_is_valid_year(2010))
        self.assertTrue(_is_valid_year(2024))
        
        # Invalid range
        self.assertFalse(_is_valid_year(1999))
        self.assertFalse(_is_valid_year(2025))
        self.assertFalse(_is_valid_year(None))

    def test_calculate_backoff(self):
        """Test exponential backoff calculation."""
        # With seed for determinism
        delay0 = _calculate_backoff(0, seed=42)
        delay1 = _calculate_backoff(1, seed=42)
        delay2 = _calculate_backoff(2, seed=42)
        
        self.assertGreater(delay1, delay0)
        self.assertGreater(delay2, delay1)
        self.assertLessEqual(delay2, 10.0) # Max backoff check

    @patch('src.data.fetch.arxiv_fetcher.requests.get')
    def test_fetch_with_retry_success(self, mock_get):
        """Test that the fetcher retries on failure and succeeds eventually."""
        # Mock response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = b"""<?xml version="1.0" encoding="UTF-8"?>
        <feed xmlns="http://www.w3.org/2005/Atom" xmlns:arxiv="http://arxiv.org/schemas/atom">
            <entry>
                <title>Test Paper</title>
                <summary>This is a test abstract.</summary>
                <published>2023-01-01T00:00:00Z</published>
                <id>http://arxiv.org/abs/2301.00001</id>
                <author><name>Test Author</name></author>
            </entry>
        </feed>"""
        
        # First call fails, second succeeds
        mock_get.side_effect = [
            Exception("Network Error"),
            mock_response
        ]

        # We need to mock time.sleep to make test fast
        with patch('src.data.fetch.arxiv_fetcher.time.sleep'):
            try:
                records = fetch_arxiv_abstracts(max_results=10, seed=42)
                # Should succeed on 2nd attempt
                self.assertEqual(len(records), 1)
            except Exception:
                self.fail("fetch_arxiv_abstracts raised exception unexpectedly")

    @patch('src.data.fetch.arxiv_fetcher.requests.get')
    def test_fetch_max_retries_exceeded(self, mock_get):
        """Test that the fetcher fails after max retries."""
        mock_get.side_effect = Exception("Persistent Network Error")
        
        with patch('src.data.fetch.arxiv_fetcher.time.sleep'):
            with self.assertRaises(RuntimeError):
                fetch_arxiv_abstracts(max_results=10, seed=42)

    def test_parse_arxiv_entry(self):
        """Test parsing of a mock XML entry."""
        xml_str = """<entry xmlns="http://www.w3.org/2005/Atom" xmlns:arxiv="http://arxiv.org/schemas/atom">
            <title>Test Paper</title>
            <summary>This is a test abstract.</summary>
            <published>2023-01-01T00:00:00Z</published>
            <id>http://arxiv.org/abs/2301.00001</id>
            <author><name>Test Author</name></author>
        </entry>"""
        
        root = ET.fromstring(xml_str)
        namespaces = {
            "atom": "http://www.w3.org/2005/Atom",
            "arxiv": "http://arxiv.org/schemas/atom"
        }
        
        record = _parse_arxiv_entry(root, namespaces)
        
        self.assertIsInstance(record, AbstractRecord)
        self.assertEqual(record.title, "Test Paper")
        self.assertEqual(record.published_year, 2023)
        self.assertEqual(record.source, "arxiv")

if __name__ == '__main__':
    unittest.main()