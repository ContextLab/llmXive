"""
Unit tests for data/download_ebd.py
"""
import os
import sys
import unittest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock
import hashlib

# Add project root to path
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from data.download_ebd import (
    list_s3_bucket,
    find_latest_parquet,
    compute_sha256,
    convert_parquet_to_csv
)

class TestDownloadEBD(unittest.TestCase):
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.test_csv_path = Path(self.temp_dir) / "test.csv"
        
    def tearDown(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_find_latest_parquet_empty_list(self):
        """Test that find_latest_parquet raises FileNotFoundError for empty list."""
        with self.assertRaises(FileNotFoundError):
            find_latest_parquet([])
    
    def test_find_latest_parquet_no_parquet_files(self):
        """Test that find_latest_parquet raises FileNotFoundError when no .parquet files exist."""
        objects = [
            {'Key': 'file1.txt', 'LastModified': '2023-01-01T00:00:00Z'},
            {'Key': 'file2.csv', 'LastModified': '2023-01-02T00:00:00Z'}
        ]
        with self.assertRaises(FileNotFoundError):
            find_latest_parquet(objects)
    
    def test_find_latest_parquet_sorts_correctly(self):
        """Test that find_latest_parquet returns the most recent file."""
        objects = [
            {'Key': 'old.parquet', 'LastModified': '2020-01-01T00:00:00Z'},
            {'Key': 'newest.parquet', 'LastModified': '2023-01-01T00:00:00Z'},
            {'Key': 'medium.parquet', 'LastModified': '2022-01-01T00:00:00Z'}
        ]
        result = find_latest_parquet(objects)
        self.assertEqual(result, 'newest.parquet')
    
    def test_compute_sha256(self):
        """Test SHA-256 computation."""
        test_content = b"Hello, World!"
        expected_hash = hashlib.sha256(test_content).hexdigest()
        
        with tempfile.NamedTemporaryFile(delete=False) as f:
            f.write(test_content)
            temp_path = Path(f.name)
        
        try:
            computed_hash = compute_sha256(temp_path)
            self.assertEqual(computed_hash, expected_hash)
        finally:
            os.unlink(temp_path)
    
    @patch('data.download_ebd.requests.get')
    def test_list_s3_bucket_parsing(self, mock_get):
        """Test S3 bucket listing XML parsing."""
        # Mock S3 XML response
        mock_response = MagicMock()
        mock_response.content = b"""<?xml version="1.0" encoding="UTF-8"?>
        <ListBucketResult xmlns="http://s3.amazonaws.com/doc/2006-03-01/">
            <Contents>
                <Key>file1.parquet</Key>
                <LastModified>2023-01-01T00:00:00Z</LastModified>
            </Contents>
            <Contents>
                <Key>file2.parquet</Key>
                <LastModified>2023-01-02T00:00:00Z</LastModified>
            </Contents>
        </ListBucketResult>"""
        mock_get.return_value = mock_response
        
        objects = list_s3_bucket("https://example.com/bucket")
        
        self.assertEqual(len(objects), 2)
        self.assertEqual(objects[0]['Key'], 'file1.parquet')
        self.assertEqual(objects[1]['Key'], 'file2.parquet')
    
    def test_convert_parquet_to_csv_missing_pandas(self):
        """Test that convert_parquet_to_csv raises ImportError when pandas is missing."""
        # Create a dummy parquet file
        parquet_path = Path(self.temp_dir) / "dummy.parquet"
        parquet_path.write_text("dummy content")
        
        with patch.dict(sys.modules, {'pandas': None}):
            with self.assertRaises(ImportError):
                convert_parquet_to_csv(parquet_path, self.test_csv_path)

if __name__ == '__main__':
    unittest.main()