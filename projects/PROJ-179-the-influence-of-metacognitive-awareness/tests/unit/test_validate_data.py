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

# Add parent directory to path to import code
sys.path.insert(0, str(Path(__file__).parent.parent))

from code.data.validate_data import validate_fields, write_report, find_input_file

class TestValidateData(unittest.TestCase):

    def test_validate_fields_pass(self):
        """Test validation passes when required fields exist."""
        df = pd.DataFrame({
            'confidence_rating': [1, 2, 3],
            'source_label': ['A', 'B', 'C'],
            'other_col': [10, 20, 30]
        })
        result = validate_fields(df)
        self.assertTrue(result)

    def test_validate_fields_missing_confidence(self):
        """Test validation fails when confidence_rating is missing."""
        df = pd.DataFrame({
            'source_label': ['A', 'B', 'C'],
            'other_col': [10, 20, 30]
        })
        with self.assertRaises(ValueError) as context:
            validate_fields(df)
        self.assertIn("confidence_rating", str(context.exception))

    def test_validate_fields_missing_source(self):
        """Test validation fails when source_label is missing."""
        df = pd.DataFrame({
            'confidence_rating': [1, 2, 3],
            'other_col': [10, 20, 30]
        })
        with self.assertRaises(ValueError) as context:
            validate_fields(df)
        self.assertIn("source_label", str(context.exception))

    def test_validate_fields_both_missing(self):
        """Test validation fails when both required fields are missing."""
        df = pd.DataFrame({
            'other_col': [10, 20, 30]
        })
        with self.assertRaises(ValueError) as context:
            validate_fields(df)
        self.assertIn("confidence_rating", str(context.exception))
        self.assertIn("source_label", str(context.exception))

    def test_write_report(self):
        """Test that write_report creates a valid JSON file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test_report.json"
            write_report("PASS", "Test message", output_path)
            
            self.assertTrue(output_path.exists())
            
            with open(output_path, 'r') as f:
                report = json.load(f)
            
            self.assertEqual(report["status"], "PASS")
            self.assertEqual(report["message"], "Test message")
            self.assertIn("fields_checked", report)

if __name__ == '__main__':
    unittest.main()