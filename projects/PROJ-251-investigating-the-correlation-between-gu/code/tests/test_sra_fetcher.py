import unittest
import pandas as pd
from unittest.mock import patch, MagicMock
from pathlib import Path
import sys
import os

# Add code to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.sra_fetcher import fetch_otu_table, fetch_serology_metadata, DataUnavailableError

class TestSRAFetcher(unittest.TestCase):

    @patch('utils.sra_fetcher.requests.get')
    def test_fetch_otu_table_success(self, mock_get):
        # Mock response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = b"subject_id,taxon_A,taxon_B\nS1,0.5,0.3\nS2,0.4,0.6"
        mock_get.return_value = mock_response

        df = fetch_otu_table("SRP123456")

        self.assertEqual(len(df), 2)
        self.assertIn('subject_id', df.columns)
        mock_get.assert_called_once()

    @patch('utils.sra_fetcher.requests.get')
    def test_fetch_otu_table_not_found(self, mock_get):
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_response.raise_for_status.side_effect = Exception("404 Client Error")
        mock_get.return_value = mock_response

        with self.assertRaises(DataUnavailableError):
            fetch_otu_table("SRP999999")

    @patch('utils.sra_fetcher.requests.get')
    def test_fetch_serology_metadata_success(self, mock_get):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = b"subject_id,titer_baseline,titer_post\nS1,10,40\nS2,5,20"
        mock_get.return_value = mock_response

        df = fetch_serology_metadata("SRP123456")

        self.assertEqual(len(df), 2)
        self.assertIn('titer_post', df.columns)
        mock_get.assert_called_once()

    @patch('utils.sra_fetcher.requests.get')
    def test_fetch_serology_metadata_missing_columns(self, mock_get):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = b"subject_id,other_col\nS1,10"
        mock_get.return_value = mock_response

        with self.assertRaises(DataUnavailableError):
            fetch_serology_metadata("SRP123456")

if __name__ == '__main__':
    unittest.main()