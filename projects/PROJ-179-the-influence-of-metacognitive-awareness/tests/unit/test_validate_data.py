"""
Unit tests for the functions defined in ``code/data/validate_data.py``.
"""

import json
import os
import tempfile
import unittest
from pathlib import Path

import pandas as pd

# Import the module under test
from data.validate_data import (
    find_input_file,
    load_dataset,
    validate_fields,
    write_report,
)

class TestValidateDataFunctions(unittest.TestCase):
    """Tests for the validation helper functions."""

    def setUp(self):
        # Create a temporary directory to act as the repository root
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.repo_root = Path(self.tmp_dir.name)

        # Create the expected raw data folder structure
        self.raw_dir = self.repo_root / "data" / "raw"
        self.raw_dir.mkdir(parents=True, exist_ok=True)

        # Patch the module's __file__ attribute so that path resolution works
        # inside the functions (they walk up two parents from __file__).
        self.original_file = data.validate_data.__file__
        data.validate_data.__file__ = str(self.repo_root / "code" / "data" / "validate_data.py")

    def tearDown(self):
        # Restore original __file__ reference
        data.validate_data.__file__ = self.original_file
        self.tmp_dir.cleanup()

    def test_find_input_file_returns_none_when_empty(self):
        self.assertIsNone(find_input_file())

    def test_find_input_file_finds_csv(self):
        csv_path = self.raw_dir / "example.csv"
        csv_path.write_text("a,b,c\n1,2,3\n")
        found = find_input_file()
        self.assertIsNotNone(found)
        self.assertTrue(found.name.endswith(".csv"))

    def test_load_dataset_success(self):
        csv_path = self.raw_dir / "data.csv"
        csv_path.write_text("col1,col2\n10,20\n")
        df = load_dataset(csv_path)
        self.assertIsInstance(df, pd.DataFrame)
        self.assertListEqual(list(df.columns), ["col1", "col2"])

    def test_validate_fields_passes(self):
        df = pd.DataFrame(
            {"confidence_rating": [0.5], "source_label": ["A"], "other": [1]}
        )
        # Should not raise
        validate_fields(df)

    def test_validate_fields_raises(self):
        df = pd.DataFrame({"confidence_rating": [0.5]})
        with self.assertRaises(ValueError):
            validate_fields(df)

    def test_write_report_creates_file(self):
        report_path = self.repo_root / "data" / "validation_report.json"
        write_report(status="PASS", report_path=report_path)
        self.assertTrue(report_path.is_file())
        with open(report_path, "r", encoding="utf-8") as f:
            content = json.load(f)
        self.assertEqual(content["status"], "PASS")

if __name__ == "__main__":
    unittest.main()