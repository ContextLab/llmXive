"""
Tests for T036: trial_synchrony_export.py
"""
import os
import sys
import unittest
import pandas as pd
import numpy as np
from pathlib import Path

# Add code directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'code'))

from trial_synchrony_export import generate_trial_level_synchrony_csv
from config import ensure_directories

class TestTrialSynchronyExport(unittest.TestCase):
    def setUp(self):
        # Ensure directories exist
        ensure_directories()
        self.output_path = os.path.join("data", "trial_level", "per_trial_synchrony.csv")
        # Remove output file if it exists
        if os.path.exists(self.output_path):
            os.remove(self.output_path)

    def test_file_creation(self):
        """Test that the CSV file is created."""
        # This test will fail if the data is not available, which is expected
        # in a real environment without T035 data.
        try:
            generate_trial_level_synchrony_csv()
            self.assertTrue(os.path.exists(self.output_path))
        except FileNotFoundError:
            # If data is not available, the function should exit with an error
            # which is the correct behavior.
            self.fail("The function should not exit with an error if data is available.")

    def test_csv_columns(self):
        """Test that the CSV has the correct columns."""
        try:
            generate_trial_level_synchrony_csv()
            df = pd.read_csv(self.output_path)
            required_columns = ['subject_id', 'trial_id', 'condition', 'synchrony', 'rt']
            self.assertListEqual(list(df.columns), required_columns)
        except FileNotFoundError:
            self.fail("The function should not exit with an error if data is available.")

    def test_no_missing_synchrony(self):
        """Test that there are no missing synchrony values in the output."""
        try:
            generate_trial_level_synchrony_csv()
            df = pd.read_csv(self.output_path)
            self.assertTrue(df['synchrony'].notna().all())
        except FileNotFoundError:
            self.fail("The function should not exit with an error if data is available.")

if __name__ == '__main__':
    unittest.main()