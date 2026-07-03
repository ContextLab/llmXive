"""
Integration test for T021: Target variable missing value validation.
"""
import os
import sys
import csv
import tempfile
import shutil
from pathlib import Path
import unittest

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "code"))

from data.validate_target import validate_target_no_missing, load_processed_data, main


class TestTargetValidation(unittest.TestCase):

    def setUp(self):
        """Set up temporary directory for test data."""
        self.temp_dir = tempfile.mkdtemp()
        self.test_file = Path(self.temp_dir) / "test_data.csv"

    def tearDown(self):
        """Clean up temporary directory."""
        shutil.rmtree(self.temp_dir)

    def create_csv(self, rows):
        """Helper to create a CSV file with given rows."""
        with open(self.test_file, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=["id", "shear_modulus_gpa", "feature1"])
            writer.writeheader()
            writer.writerows(rows)

    def test_no_missing_values(self):
        """Test that valid data passes validation."""
        self.create_csv([
            {"id": "1", "shear_modulus_gpa": "35.5", "feature1": "0.1"},
            {"id": "2", "shear_modulus_gpa": "42.0", "feature1": "0.2"},
            {"id": "3", "shear_modulus_gpa": "38.2", "feature1": "0.3"},
        ])

        data = load_processed_data(str(self.test_file))
        report = validate_target_no_missing(data)

        self.assertTrue(report["valid"])
        self.assertEqual(report["missing_count"], 0)
        self.assertEqual(report["total_rows"], 3)

    def test_missing_none_value(self):
        """Test detection of None values."""
        self.create_csv([
            {"id": "1", "shear_modulus_gpa": "35.5", "feature1": "0.1"},
            {"id": "2", "shear_modulus_gpa": "", "feature1": "0.2"}, # Empty string
            {"id": "3", "shear_modulus_gpa": "38.2", "feature1": "0.3"},
        ])

        data = load_processed_data(str(self.test_file))
        report = validate_target_no_missing(data)

        self.assertFalse(report["valid"])
        self.assertEqual(report["missing_count"], 1)
        self.assertIn(1, report["missing_indices"])

    def test_missing_nan_string(self):
        """Test detection of 'nan' string values."""
        self.create_csv([
            {"id": "1", "shear_modulus_gpa": "35.5", "feature1": "0.1"},
            {"id": "2", "shear_modulus_gpa": "nan", "feature1": "0.2"},
            {"id": "3", "shear_modulus_gpa": "38.2", "feature1": "0.3"},
        ])

        data = load_processed_data(str(self.test_file))
        report = validate_target_no_missing(data)

        self.assertFalse(report["valid"])
        self.assertEqual(report["missing_count"], 1)

    def test_missing_na_string(self):
        """Test detection of 'na' string values."""
        self.create_csv([
            {"id": "1", "shear_modulus_gpa": "35.5", "feature1": "0.1"},
            {"id": "2", "shear_modulus_gpa": "NA", "feature1": "0.2"},
            {"id": "3", "shear_modulus_gpa": "38.2", "feature1": "0.3"},
        ])

        data = load_processed_data(str(self.test_file))
        report = validate_target_no_missing(data)

        self.assertFalse(report["valid"])
        self.assertEqual(report["missing_count"], 1)

    def test_all_missing(self):
        """Test when all target values are missing."""
        self.create_csv([
            {"id": "1", "shear_modulus_gpa": "", "feature1": "0.1"},
            {"id": "2", "shear_modulus_gpa": "nan", "feature1": "0.2"},
            {"id": "3", "shear_modulus_gpa": "null", "feature1": "0.3"},
        ])

        data = load_processed_data(str(self.test_file))
        report = validate_target_no_missing(data)

        self.assertFalse(report["valid"])
        self.assertEqual(report["missing_count"], 3)
        self.assertEqual(report["total_rows"], 3)

if __name__ == "__main__":
    unittest.main()