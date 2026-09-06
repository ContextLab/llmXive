import unittest
import pandas as pd
from unittest.mock import patch, MagicMock, mock_open
from pathlib import Path
import sys
import os

# Ensure code/ is in path
sys.path.insert(0, 'code')

from utils.sra_fetcher import DataUnavailableError, fetch_otu_table, fetch_serology_metadata, write_sra_status
from utils.logging_config import get_logger

logger = get_logger(__name__)

class TestSRAFetcher(unittest.TestCase):

    @patch('utils.sra_fetcher.requests.head')
    @patch('utils.sra_fetcher.requests.get')
    def test_fetch_otu_table_success(self, mock_get, mock_head):
        """Test successful fetch of OTU table."""
        # Mock HEAD request to return 200
        mock_head.return_value.status_code = 200
        # Mock GET request to return CSV content
        mock_response = MagicMock()
        mock_response.content = b"subject_id,taxon_A,taxon_B\nS1,10,20\nS2,15,25\n"
        mock_get.return_value = mock_response
        
        output_path = Path("data/raw/test_otu.csv")
        # Ensure directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            result_path = fetch_otu_table("SRP123456", output_path)
            self.assertTrue(result_path.exists())
            df = pd.read_csv(result_path)
            self.assertIn("subject_id", df.columns)
            self.assertIn("taxon_A", df.columns)
        finally:
            if result_path.exists():
                result_path.unlink()

    @patch('utils.sra_fetcher.requests.head')
    def test_fetch_otu_table_not_found(self, mock_head):
        """Test fetch fails when file not found."""
        # Mock HEAD request to return 404 for all attempts
        mock_head.return_value.status_code = 404
        
        output_path = Path("data/raw/test_otu_fail.csv")
        
        with self.assertRaises(DataUnavailableError) as context:
            fetch_otu_table("SRP999999", output_path)
        
        self.assertIn("not found", str(context.exception))

    @patch('utils.sra_fetcher.requests.head')
    @patch('utils.sra_fetcher.requests.get')
    def test_fetch_serology_success(self, mock_get, mock_head):
        """Test successful fetch of serology metadata."""
        mock_head.return_value.status_code = 200
        mock_response = MagicMock()
        mock_response.content = b"subject_id,titer_baseline,titer_post\nS1,100,400\nS2,200,800\n"
        mock_get.return_value = mock_response
        
        output_path = Path("data/raw/test_serology.csv")
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            result_path = fetch_serology_metadata("SRP123456", output_path)
            self.assertTrue(result_path.exists())
            df = pd.read_csv(result_path)
            self.assertIn("subject_id", df.columns)
            self.assertIn("titer_baseline", df.columns)
            self.assertIn("titer_post", df.columns)
        finally:
            if result_path.exists():
                result_path.unlink()

    def test_write_sra_status(self):
        """Test writing sra_status.json."""
        status_dir = Path("data/research")
        status_dir.mkdir(parents=True, exist_ok=True)
        
        try:
            write_sra_status("real_data_found", False, "SRP123456")
            status_file = status_dir / "sra_status.json"
            self.assertTrue(status_file.exists())
            
            import json
            with open(status_file) as f:
                data = json.load(f)
            
            self.assertEqual(data["status"], "real_data_found")
            self.assertFalse(data["use_synthetic"])
            self.assertEqual(data["accession"], "SRP123456")
        finally:
            if status_file.exists():
                status_file.unlink()

if __name__ == "__main__":
    unittest.main()
