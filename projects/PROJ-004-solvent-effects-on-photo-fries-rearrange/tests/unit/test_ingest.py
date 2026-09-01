"""
Unit tests for code/data/ingest.py
"""

import os
import sys
import tempfile
import unittest
from pathlib import Path
import pandas as pd

# Add code to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from data.ingest import ingest_real_transient_absorption_data


class TestIngestRealData(unittest.TestCase):
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.test_file = Path(self.temp_dir.name) / "test_traces.csv"
        
        # Create a valid test CSV
        data = {
            "time": [0, 10, 20, 30],
            "wavelength": [400, 400, 400, 400],
            "absorbance": [1.0, 0.8, 0.6, 0.4]
        }
        df = pd.DataFrame(data)
        df.to_csv(self.test_file, index=False)
    
    def tearDown(self):
        """Clean up test fixtures."""
        self.temp_dir.cleanup()
    
    def test_ingest_existing_file(self):
        """Test ingestion of an existing file."""
        df = ingest_real_transient_absorption_data(str(self.test_file))
        self.assertEqual(len(df), 4)
        self.assertIn("time", df.columns)
        self.assertIn("absorbance", df.columns)
    
    def test_ingest_missing_file_real_mode(self):
        """Test that missing file raises FileNotFoundError when USE_REAL_DATA=true."""
        os.environ["USE_REAL_DATA"] = "true"
        missing_path = str(Path(self.temp_dir.name) / "nonexistent.csv")
        
        with self.assertRaises(FileNotFoundError) as context:
            ingest_real_transient_absorption_data(missing_path)
        
        self.assertIn("CRITICAL", str(context.exception))
        self.assertIn("USE_REAL_DATA", str(context.exception))
        
        # Clean up env
        del os.environ["USE_REAL_DATA"]
    
    def test_ingest_missing_file_normal_mode(self):
        """Test behavior when file is missing and USE_REAL_DATA is not set."""
        if "USE_REAL_DATA" in os.environ:
            del os.environ["USE_REAL_DATA"]
        
        missing_path = str(Path(self.temp_dir.name) / "nonexistent.csv")
        
        # Should raise FileNotFoundError because this function is for REAL data only
        with self.assertRaises(FileNotFoundError):
            ingest_real_transient_absorption_data(missing_path)
    
    def test_ingest_empty_file(self):
        """Test ingestion of an empty file."""
        empty_file = Path(self.temp_dir.name) / "empty.csv"
        empty_file.touch()
        
        with self.assertRaises(ValueError) as context:
            ingest_real_transient_absorption_data(str(empty_file))
        
        self.assertIn("empty", str(context.exception))
    
    def test_ingest_missing_columns(self):
        """Test ingestion of file missing required columns."""
        bad_file = Path(self.temp_dir.name) / "bad.csv"
        pd.DataFrame({"x": [1, 2, 3]}).to_csv(bad_file, index=False)
        
        with self.assertRaises(ValueError) as context:
            ingest_real_transient_absorption_data(str(bad_file))
        
        self.assertIn("missing", str(context.exception).lower())
    
    def test_default_path(self):
        """Test that default path is used when no path is provided."""
        # This is harder to test without mocking the config,
        # but we can at least verify the function signature accepts None
        # and doesn't crash immediately (it will fail on file not found)
        if "USE_REAL_DATA" in os.environ:
            del os.environ["USE_REAL_DATA"]
        
        with self.assertRaises(FileNotFoundError):
            ingest_real_transient_absorption_data(None)


if __name__ == "__main__":
    unittest.main()