"""
Unit tests for merge_datasets.py (T012c).
"""

import os
import sys
import tempfile
import unittest
from pathlib import Path
import pandas as pd

# Add code directory to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "code"))

from merge_datasets import load_csv_safe, merge_perovskite_datasets, remove_duplicates

class TestMergeDatasets(unittest.TestCase):

    def setUp(self):
        """Set up temporary files for testing."""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.nrel_path = Path(self.temp_dir.name) / "nrel_perovskites.csv"
        self.mp_path = Path(self.temp_dir.name) / "mp_perovskites.csv"

    def tearDown(self):
        """Clean up temporary files."""
        self.temp_dir.cleanup()

    def test_load_csv_safe_missing_file(self):
        """Test loading a non-existent file returns None."""
        result = load_csv_safe(Path("non_existent_file.csv"))
        self.assertIsNone(result)

    def test_load_csv_safe_empty_file(self):
        """Test loading an empty file returns None."""
        self.nrel_path.touch()  # Create empty file
        result = load_csv_safe(self.nrel_path)
        self.assertIsNone(result)

    def test_load_csv_safe_valid(self):
        """Test loading a valid CSV file."""
        df = pd.DataFrame({"formula": ["ABX3"], "source": ["NREL"]})
        df.to_csv(self.nrel_path, index=False)
        result = load_csv_safe(self.nrel_path)
        self.assertIsNotNone(result)
        self.assertEqual(len(result), 1)

    def test_merge_perovskite_datasets(self):
        """Test concatenating two DataFrames."""
        nrel_df = pd.DataFrame({"formula": ["A1"], "source": ["NREL"], "val": [1]})
        mp_df = pd.DataFrame({"formula": ["A2"], "source": ["MP"], "val": [2]})
        merged = merge_perovskite_datasets(nrel_df, mp_df)
        self.assertEqual(len(merged), 2)
        self.assertTrue("formula" in merged.columns)
        self.assertTrue("source" in merged.columns)

    def test_remove_duplicates(self):
        """Test duplicate removal logic."""
        df = pd.DataFrame({
            "formula": ["A1", "A1", "A2"],
            "source": ["NREL", "NREL", "MP"],
            "val": [1, 1, 2]
        })
        deduped, count = remove_duplicates(df)
        self.assertEqual(count, 1)
        self.assertEqual(len(deduped), 2)

    def test_remove_duplicates_no_duplicates(self):
        """Test when there are no duplicates."""
        df = pd.DataFrame({
            "formula": ["A1", "A2"],
            "source": ["NREL", "MP"],
            "val": [1, 2]
        })
        deduped, count = remove_duplicates(df)
        self.assertEqual(count, 0)
        self.assertEqual(len(deduped), 2)

    def test_remove_duplicates_missing_columns(self):
        """Test that missing columns raise an error."""
        df = pd.DataFrame({"formula": ["A1"], "val": [1]})
        with self.assertRaises(ValueError):
            remove_duplicates(df)

if __name__ == "__main__":
    unittest.main()