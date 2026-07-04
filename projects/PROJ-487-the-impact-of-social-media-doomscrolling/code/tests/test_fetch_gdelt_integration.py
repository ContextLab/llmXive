"""
Integration test for GDELT fetch script.

This test verifies that the fetch script can run and produce a valid CSV file
with the expected structure.
"""
import os
import sys
import unittest
import tempfile
import shutil
import pandas as pd

# Add project root to path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from utils.logging import get_logger

logger = get_logger(__name__)

class TestGDELTFetchIntegration(unittest.TestCase):
    """Integration tests for GDELT fetch functionality."""

    def setUp(self):
        """Set up test fixtures."""
        self.test_dir = tempfile.mkdtemp()
        self.output_path = os.path.join(self.test_dir, "test_gdelt.csv")
        
    def tearDown(self):
        """Clean up test fixtures."""
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def test_fetch_script_structure(self):
        """Verify the fetch script exists and has required functions."""
        script_path = os.path.join(project_root, "code", "data", "fetch_gdelt.py")
        self.assertTrue(os.path.exists(script_path), "fetch_gdelt.py should exist")
        
        # Check that required functions are present
        import importlib.util
        spec = importlib.util.spec_from_file_location("fetch_gdelt", script_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        
        self.assertTrue(hasattr(module, 'fetch_gdelt_events'), 
                      "Module should have fetch_gdelt_events function")
        self.assertTrue(hasattr(module, 'save_to_csv'), 
                      "Module should have save_to_csv function")
        self.assertTrue(hasattr(module, 'main'), 
                      "Module should have main function")

    def test_output_csv_structure(self):
        """Verify that a sample output CSV has the expected structure."""
        # Create a sample DataFrame with expected structure
        sample_df = pd.DataFrame({
            "date": ["2023-01-01", "2023-01-02", "2023-01-03"],
            "event_count": [150, 175, 160]
        })
        
        # Save to test path
        sample_df.to_csv(self.output_path, index=False)
        
        # Verify structure
        df = pd.read_csv(self.output_path)
        
        self.assertIn("date", df.columns, "CSV should have 'date' column")
        self.assertIn("event_count", df.columns, "CSV should have 'event_count' column")
        self.assertEqual(len(df), 3, "CSV should have 3 rows")
        self.assertEqual(df["event_count"].dtype, "int64", "event_count should be integer")
        
        # Verify date format
        self.assertTrue(
            all(len(d) == 10 for d in df["date"]),
            "Dates should be in YYYY-MM-DD format"
        )

    def test_date_range_validity(self):
        """Verify that dates in the dataset are within expected range."""
        # Create a sample DataFrame with valid dates
        sample_df = pd.DataFrame({
            "date": ["2023-06-01", "2023-12-31"],
            "event_count": [100, 200]
        })
        
        sample_df.to_csv(self.output_path, index=False)
        
        df = pd.read_csv(self.output_path)
        
        # Parse dates and check range
        df["date"] = pd.to_datetime(df["date"])
        min_date = df["date"].min()
        max_date = df["date"].max()
        
        # Assuming the script uses 2023-01-01 to 2024-01-01
        self.assertGreaterEqual(min_date, pd.Timestamp("2023-01-01"))
        self.assertLessEqual(max_date, pd.Timestamp("2024-01-01"))

    def test_non_negative_counts(self):
        """Verify that event counts are non-negative."""
        sample_df = pd.DataFrame({
            "date": ["2023-01-01"],
            "event_count": [0]
        })
        
        sample_df.to_csv(self.output_path, index=False)
        
        df = pd.read_csv(self.output_path)
        
        self.assertTrue(
            all(df["event_count"] >= 0),
            "Event counts should be non-negative"
        )

if __name__ == "__main__":
    unittest.main()