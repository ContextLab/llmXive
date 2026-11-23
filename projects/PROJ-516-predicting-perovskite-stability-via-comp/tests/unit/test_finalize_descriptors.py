"""
Unit tests for T012e: finalize_descriptors.py
"""

import unittest
import tempfile
import os
from pathlib import Path
import pandas as pd
import shutil

# Add parent directory to path to import the module
sys_path = Path(__file__).resolve().parent.parent.parent / "code"
import sys
if str(sys_path) not in sys.path:
    sys.path.insert(0, str(sys_path))

from finalize_descriptors import load_csv_safe, remove_duplicates, merge_perovskite_datasets

class TestFinalizeDescriptors(unittest.TestCase):
    
    def setUp(self):
        """Create a temporary directory for test files."""
        self.test_dir = tempfile.mkdtemp()
        self.test_dir_path = Path(self.test_dir)

    def tearDown(self):
        """Clean up the temporary directory."""
        shutil.rmtree(self.test_dir)

    def test_load_csv_safe_exists(self):
        """Test loading an existing CSV file."""
        file_path = self.test_dir_path / "test.csv"
        df = pd.DataFrame({"a": [1, 2], "b": [3, 4]})
        df.to_csv(file_path, index=False)
        
        loaded_df = load_csv_safe(file_path)
        pd.testing.assert_frame_equal(loaded_df, df)

    def test_load_csv_safe_not_exists(self):
        """Test loading a non-existent CSV file raises FileNotFoundError."""
        file_path = self.test_dir_path / "non_existent.csv"
        with self.assertRaises(FileNotFoundError):
            load_csv_safe(file_path)

    def test_load_csv_safe_empty(self):
        """Test loading an empty CSV file raises ValueError."""
        file_path = self.test_dir_path / "empty.csv"
        file_path.touch() # Create empty file
        
        with self.assertRaises(ValueError):
            load_csv_safe(file_path)

    def test_remove_duplicates(self):
        """Test duplicate removal logic."""
        df = pd.DataFrame({
            "formula": ["ABX3", "ABX3", "CDY2"],
            "source": ["NREL", "NREL", "MaterialsProject"],
            "value": [1, 2, 3]
        })
        
        result = remove_duplicates(df)
        expected = pd.DataFrame({
            "formula": ["ABX3", "CDY2"],
            "source": ["NREL", "MaterialsProject"],
            "value": [1, 3]
        })
        
        pd.testing.assert_frame_equal(result.reset_index(drop=True), expected.reset_index(drop=True))

    def test_merge_perovskite_datasets(self):
        """Test merging two datasets."""
        nrel_path = self.test_dir_path / "nrel.csv"
        mp_path = self.test_dir_path / "mp.csv"
        
        nrel_df = pd.DataFrame({"formula": ["ABX3"], "T_d": [500]})
        mp_df = pd.DataFrame({"formula": ["CDY2"], "T_d": [600]})
        
        nrel_df.to_csv(nrel_path, index=False)
        mp_df.to_csv(mp_path, index=False)
        
        merged = merge_perovskite_datasets(nrel_path, mp_path)
        
        self.assertEqual(len(merged), 2)
        self.assertIn("source", merged.columns)
        self.assertTrue(merged["source"].isin(["NREL", "MaterialsProject"]).all())

if __name__ == "__main__":
    unittest.main()