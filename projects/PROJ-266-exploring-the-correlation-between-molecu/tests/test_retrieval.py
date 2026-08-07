"""
Unit tests for data filtering logic in code/data/preprocessing.py.
Tests verify filtering logic and pass rate calculation as required by T011.
"""

import csv
import os
import tempfile
from pathlib import Path
from unittest import TestCase, main as unittest_main

import sys

# Ensure code/ is in path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from code.data.preprocessing import load_raw_data, preprocess_data, write_clean_data


class TestPreprocessingLogic(TestCase):
    """Tests for the data filtering logic in preprocessing.py."""

    def setUp(self):
        """Set up temporary directories and test data."""
        self.temp_dir = tempfile.mkdtemp()
        self.raw_path = os.path.join(self.temp_dir, "raw_data.csv")
        self.clean_path = os.path.join(self.temp_dir, "clean_data.csv")
        
        # Create a realistic raw dataset with various edge cases
        self.raw_data = [
            {"smiles": "CCO", "logPapp": -4.5, "mw": 46.07, "psa": 20.23, "assay_id": "1"},
            {"smiles": "CCCC", "logPapp": -3.2, "mw": 58.12, "psa": 0.0, "assay_id": "2"},
            {"smiles": "", "logPapp": -4.0, "mw": 100.0, "psa": 10.0, "assay_id": "3"},  # Empty SMILES
            {"smiles": "C1=CC=CC=C1", "logPapp": None, "mw": 78.11, "psa": 0.0, "assay_id": "4"},  # NULL logPapp
            {"smiles": None, "logPapp": -5.0, "mw": 80.0, "psa": 5.0, "assay_id": "5"},  # NULL SMILES
            {"smiles": "CC(=O)O", "logPapp": -2.8, "mw": 60.05, "psa": 37.3, "assay_id": "6"},
            {"smiles": "NaN", "logPapp": -4.1, "mw": 90.0, "psa": 15.0, "assay_id": "7"},  # Invalid SMILES string
            {"smiles": "CCN", "logPapp": "invalid", "mw": 45.08, "psa": 12.03, "assay_id": "8"},  # Invalid logPapp
        ]
        
        # Write raw data to file
        with open(self.raw_path, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=self.raw_data[0].keys())
            writer.writeheader()
            writer.writerows(self.raw_data)

    def tearDown(self):
        """Clean up temporary files."""
        if os.path.exists(self.raw_path):
            os.remove(self.raw_path)
        if os.path.exists(self.clean_path):
            os.remove(self.clean_path)
        os.rmdir(self.temp_dir)

    def test_load_raw_data(self):
        """Test that raw data is loaded correctly."""
        data = load_raw_data(self.raw_path)
        self.assertEqual(len(data), len(self.raw_data))
        self.assertIn("smiles", data[0])
        self.assertIn("logPapp", data[0])

    def test_filtering_logic_non_null_smiles(self):
        """Test that records with NULL/empty SMILES are filtered out."""
        data = load_raw_data(self.raw_path)
        filtered_data, stats = preprocess_data(data)
        
        # Should exclude: empty string, None, and "NaN"
        expected_count = len(self.raw_data) - 3  # 3 invalid SMILES
        self.assertEqual(len(filtered_data), expected_count)
        
        # Verify all remaining SMILES are valid
        for record in filtered_data:
            smiles = record.get("smiles")
            self.assertIsNotNone(smiles)
            self.assertNotEqual(smiles, "")
            self.assertNotEqual(smiles, "NaN")

    def test_filtering_logic_non_null_logpapp(self):
        """Test that records with NULL logPapp are filtered out."""
        data = load_raw_data(self.raw_path)
        filtered_data, stats = preprocess_data(data)
        
        # Should exclude: None logPapp and "invalid" string
        expected_count = len(self.raw_data) - 3  # 3 invalid logPapp (including NaN/None/invalid)
        # Actually: None (1), "invalid" (1) = 2, plus 3 invalid SMILES = 5 excluded total
        # But some records might have both issues, so we check the actual count
        
        # Verify all remaining logPapp are valid numbers
        for record in filtered_data:
            logpapp = record.get("logPapp")
            self.assertIsNotNone(logpapp)
            self.assertIsInstance(logpapp, (int, float))

    def test_pass_rate_calculation(self):
        """Test that pass rate is calculated correctly."""
        data = load_raw_data(self.raw_path)
        total_records = len(data)
        
        # Count valid records manually
        valid_count = 0
        for record in data:
            smiles = record.get("smiles")
            logpapp = record.get("logPapp")
            
            if smiles and smiles != "NaN" and smiles != "":
                if logpapp is not None and isinstance(logpapp, (int, float)):
                    valid_count += 1
        
        filtered_data, stats = preprocess_data(data)
        
        expected_pass_rate = valid_count / total_records
        actual_pass_rate = stats["pass_rate"]
        
        self.assertAlmostEqual(actual_pass_rate, expected_pass_rate, places=5)
        self.assertEqual(stats["total_records"], total_records)
        self.assertEqual(stats["passed_records"], valid_count)
        self.assertEqual(stats["excluded_records"], total_records - valid_count)

    def test_excluded_records_breakdown(self):
        """Test that excluded records are categorized correctly."""
        data = load_raw_data(self.raw_path)
        _, stats = preprocess_data(data)
        
        self.assertIn("excluded_invalid_smiles", stats)
        self.assertIn("excluded_invalid_logpapp", stats)
        self.assertIn("excluded_protocol_heterogeneity", stats)
        
        # At least some records should be excluded for invalid SMILES or logPapp
        self.assertGreater(stats["excluded_invalid_smiles"] + stats["excluded_invalid_logpapp"], 0)

    def test_write_clean_data(self):
        """Test that clean data is written correctly."""
        data = load_raw_data(self.raw_path)
        filtered_data, stats = preprocess_data(data)
        
        write_clean_data(filtered_data, self.clean_path)
        
        self.assertTrue(os.path.exists(self.clean_path))
        
        with open(self.clean_path, 'r') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        
        self.assertEqual(len(rows), len(filtered_data))
        # Verify all rows have valid data
        for row in rows:
            self.assertIsNotNone(row.get("smiles"))
            self.assertIsNotNone(row.get("logPapp"))
            self.assertNotEqual(row.get("smiles"), "")

    def test_preprocess_data_integration(self):
        """Integration test: load, filter, and write in one flow."""
        # Load raw data
        raw_data = load_raw_data(self.raw_path)
        
        # Preprocess
        clean_data, stats = preprocess_data(raw_data)
        
        # Write clean data
        write_clean_data(clean_data, self.clean_path)
        
        # Verify output
        self.assertTrue(os.path.exists(self.clean_path))
        
        with open(self.clean_path, 'r') as f:
            reader = csv.DictReader(f)
            output_rows = list(reader)
        
        # All output rows should be valid
        for row in output_rows:
            smiles = row.get("smiles")
            logpapp = row.get("logPapp")
            
            self.assertIsNotNone(smiles)
            self.assertNotEqual(smiles, "")
            self.assertNotEqual(smiles, "NaN")
            
            self.assertIsNotNone(logpapp)
            self.assertIsInstance(logpapp, (int, float))


if __name__ == "__main__":
    unittest_main()