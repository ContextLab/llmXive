"""
Unit tests for src.data.loaders module.
"""
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock
import pandas as pd
import hashlib

from src.data.loaders import (
    _calculate_sha256,
    verify_data_integrity,
    load_station_data,
    load_multiple_stations
)

class TestLoaders(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.temp_path = Path(self.temp_dir.name)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_calculate_sha256(self):
        """Test SHA-256 calculation."""
        test_file = self.temp_path / "test.txt"
        test_content = b"Hello, World!"
        test_file.write_bytes(test_content)
        
        expected_hash = hashlib.sha256(test_content).hexdigest()
        actual_hash = _calculate_sha256(test_file)
        
        self.assertEqual(actual_hash, expected_hash)

    def test_verify_data_integrity_match(self):
        """Test integrity verification when hashes match."""
        test_file = self.temp_path / "test.txt"
        test_content = b"Hello, World!"
        test_file.write_bytes(test_content)
        
        expected_hash = hashlib.sha256(test_content).hexdigest()
        result = verify_data_integrity(test_file, expected_hash)
        
        self.assertTrue(result)

    def test_verify_data_integrity_mismatch(self):
        """Test integrity verification when hashes do not match."""
        test_file = self.temp_path / "test.txt"
        test_content = b"Hello, World!"
        test_file.write_bytes(test_content)
        
        wrong_hash = "0000000000000000000000000000000000000000000000000000000000000000"
        result = verify_data_integrity(test_file, wrong_hash)
        
        self.assertFalse(result)

    def test_verify_data_integrity_file_not_found(self):
        """Test integrity verification when file does not exist."""
        non_existent_file = self.temp_path / "non_existent.txt"
        
        with self.assertRaises(FileNotFoundError):
            verify_data_integrity(non_existent_file)

    def test_load_station_data_csv(self):
        """Test loading a CSV file."""
        csv_file = self.temp_path / "test.csv"
        df = pd.DataFrame({"col1": [1, 2], "col2": [3, 4]})
        df.to_csv(csv_file, index=False)
        
        result = load_station_data(csv_file)
        
        self.assertEqual(result['format'], 'csv')
        self.assertEqual(result['data'].shape, (2, 2))
        self.assertIn('hash', result)

    def test_load_station_data_parquet(self):
        """Test loading a Parquet file."""
        parquet_file = self.temp_path / "test.parquet"
        df = pd.DataFrame({"col1": [1, 2], "col2": [3, 4]})
        df.to_parquet(parquet_file)
        
        result = load_station_data(parquet_file)
        
        self.assertEqual(result['format'], 'parquet')
        self.assertEqual(result['data'].shape, (2, 2))
        self.assertIn('hash', result)

    def test_load_station_data_json(self):
        """Test loading a JSON file."""
        json_file = self.temp_path / "test.json"
        data = {"key": "value"}
        with open(json_file, 'w') as f:
            import json
            json.dump(data, f)
        
        result = load_station_data(json_file)
        
        self.assertEqual(result['format'], 'json')
        self.assertEqual(result['data'], data)
        self.assertIn('hash', result)

    def test_load_multiple_stations(self):
        """Test loading multiple station files."""
        file1 = self.temp_path / "test1.csv"
        file2 = self.temp_path / "test2.csv"
        
        df = pd.DataFrame({"col1": [1, 2]})
        df.to_csv(file1, index=False)
        df.to_csv(file2, index=False)
        
        results = load_multiple_stations([file1, file2])
        
        self.assertEqual(len(results), 2)
        for result in results:
            self.assertIn('data', result)

    def test_load_multiple_stations_with_missing_file(self):
        """Test loading multiple station files with one missing."""
        file1 = self.temp_path / "test1.csv"
        file2 = self.temp_path / "non_existent.csv"
        
        df = pd.DataFrame({"col1": [1, 2]})
        df.to_csv(file1, index=False)
        
        results = load_multiple_stations([file1, file2])
        
        # Should only return the result for the existing file
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['data'].shape, (2, 1))

    def test_load_station_data_unsupported_format(self):
        """Test loading an unsupported file format."""
        unsupported_file = self.temp_path / "test.txt"
        unsupported_file.write_text("Hello, World!")
        
        with self.assertRaises(ValueError):
            load_station_data(unsupported_file)

if __name__ == '__main__':
    unittest.main()