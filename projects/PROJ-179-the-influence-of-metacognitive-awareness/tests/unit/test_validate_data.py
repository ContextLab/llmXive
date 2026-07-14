"""
Unit tests for T006: data/validate_data.py
"""
import os
import sys
import json
import tempfile
import unittest
from pathlib import Path
import pandas as pd

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "code"))

from data.validate_data import find_input_file, load_dataset, validate_fields, write_report

class TestValidateData(unittest.TestCase):

    def setUp(self):
        """Create temporary directory structure for testing."""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.raw_dir = Path(self.temp_dir.name) / "raw"
        self.raw_dir.mkdir(parents=True)
        self.data_dir = Path(self.temp_dir.name)
        
        # Patch the global paths in the module temporarily
        import data.validate_data as vd
        self.original_raw_dir = vd.RAW_DIR
        self.original_data_dir = vd.DATA_DIR
        self.original_report_path = vd.REPORT_PATH
        
        vd.RAW_DIR = self.raw_dir
        vd.DATA_DIR = self.data_dir
        vd.REPORT_PATH = self.data_dir / "validation_report.json"

    def tearDown(self):
        """Restore original paths and cleanup temp dir."""
        import data.validate_data as vd
        vd.RAW_DIR = self.original_raw_dir
        vd.DATA_DIR = self.original_data_dir
        vd.REPORT_PATH = self.original_report_path
        self.temp_dir.cleanup()

    def test_find_input_file_missing(self):
        """Test find_input_file when no CSV exists."""
        result = find_input_file()
        self.assertIsNone(result)

    def test_find_input_file_found(self):
        """Test find_input_file finds a CSV."""
        test_file = self.raw_dir / "test.csv"
        test_file.touch()
        result = find_input_file()
        self.assertIsNotNone(result)
        self.assertEqual(result.name, "test.csv")

    def test_load_dataset(self):
        """Test loading a valid CSV."""
        test_file = self.raw_dir / "data.csv"
        df_expected = pd.DataFrame({
            'confidence_rating': [1, 2, 3],
            'source_label': ['A', 'B', 'C'],
            'other': [10, 20, 30]
        })
        df_expected.to_csv(test_file, index=False)
        
        df_loaded = load_dataset(test_file)
        self.assertEqual(len(df_loaded), 3)
        self.assertIn('confidence_rating', df_loaded.columns)

    def test_validate_fields_pass(self):
        """Test validation passes with required fields."""
        df = pd.DataFrame({
            'confidence_rating': [1, 2],
            'source_label': ['A', 'B']
        })
        result = validate_fields(df)
        self.assertTrue(result)

    def test_validate_fields_fail_missing_confidence(self):
        """Test validation fails if confidence_rating is missing."""
        df = pd.DataFrame({
            'source_label': ['A', 'B'],
            'other': [1, 2]
        })
        with self.assertRaises(ValueError) as context:
            validate_fields(df)
        self.assertIn("confidence_rating", str(context.exception))

    def test_validate_fields_fail_missing_source(self):
        """Test validation fails if source_label is missing."""
        df = pd.DataFrame({
            'confidence_rating': [1, 2],
            'other': [1, 2]
        })
        with self.assertRaises(ValueError) as context:
            validate_fields(df)
        self.assertIn("source_label", str(context.exception))

    def test_write_report(self):
        """Test writing the validation report."""
        write_report("PASS", "All good", {"count": 10})
        report_path = self.data_dir / "validation_report.json"
        self.assertTrue(report_path.exists())
        
        with open(report_path, 'r') as f:
            report = json.load(f)
        
        self.assertEqual(report["status"], "PASS")
        self.assertEqual(report["message"], "All good")
        self.assertEqual(report["details"]["count"], 10)

if __name__ == '__main__':
    unittest.main()