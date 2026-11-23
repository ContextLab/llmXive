"""
Unit tests for Dst index ingestion logic.
"""
import os
import sys
import unittest
from unittest.mock import patch, MagicMock
import csv
import io

# Add parent directory to path to import ingest module
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'code'))

from ingest import fetch_dst_indices_http, write_dst_data, DataFetchError

class TestDstIngestion(unittest.TestCase):
    
    def test_fetch_dst_indices_http_parsing(self):
        """Test that Dst data is correctly parsed from mock response."""
        mock_response = """
        # Dst Index
        2023 01 01 00 00 -15
        2023 01 01 01 00 -20
        2023 01 01 02 00 -10
        """
        
        with patch('ingest.fetch_with_backoff', return_value=mock_response.strip()):
            data = fetch_dst_indices_http()
            
        self.assertEqual(len(data), 3)
        self.assertEqual(data[0]['year'], 2023)
        self.assertEqual(data[0]['dst_value'], -15.0)
        self.assertEqual(data[0]['timestamp'], '2023-01-01T00:00:00')
        
    def test_write_dst_data_creates_file(self):
        """Test that write_dst_data creates a valid CSV file."""
        test_data = [
            {"timestamp": "2023-01-01T00:00:00", "year": 2023, "month": 1, "day": 1, "hour": 0, "minute": 0, "dst_value": -15.0},
            {"timestamp": "2023-01-01T01:00:00", "year": 2023, "month": 1, "day": 1, "hour": 1, "minute": 0, "dst_value": -20.0}
        ]
        output_path = "data/raw/test_dst_indices.csv"
        
        try:
            write_dst_data(test_data, output_path)
            self.assertTrue(os.path.exists(output_path))
            
            with open(output_path, 'r') as f:
                reader = csv.DictReader(f)
                rows = list(reader)
                
            self.assertEqual(len(rows), 2)
            self.assertEqual(rows[0]['dst_value'], '-15.0')
        finally:
            if os.path.exists(output_path):
                os.remove(output_path)
                
    def test_fetch_dst_raises_on_empty(self):
        """Test that fetch_dst_indices_http raises DataFetchError on empty response."""
        mock_response = "# Only comments\n"
        
        with patch('ingest.fetch_with_backoff', return_value=mock_response):
            with self.assertRaises(DataFetchError):
                fetch_dst_indices_http()

if __name__ == '__main__':
    unittest.main()