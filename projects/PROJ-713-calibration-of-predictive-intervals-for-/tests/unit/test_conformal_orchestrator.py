"""
Unit tests for the conformal orchestrator module.
"""
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock
import pandas as pd
import numpy as np

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from calibration.conformal_orchestrator import (
    load_evaluation_results,
    run_conformal_calibration,
    save_conformal_results
)
from config import Config
from utils.exceptions import DataValidationError


class TestConformalOrchestrator(unittest.TestCase):

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.results_dir = Path(self.temp_dir.name)
        self.coverage_csv = self.results_dir / "coverage.csv"

        # Create a mock config
        self.mock_config = MagicMock(spec=Config)
        self.mock_config.paths.results = self.results_dir

    def tearDown(self):
        """Clean up test fixtures."""
        self.temp_dir.cleanup()

    def test_load_evaluation_results_file_not_found(self):
        """Test that load_evaluation_results raises error if file missing."""
        with self.assertRaises(DataValidationError) as context:
            load_evaluation_results(self.mock_config)
        self.assertIn("Input file not found", str(context.exception))

    def test_load_evaluation_results_empty_file(self):
        """Test that load_evaluation_results raises error if file is empty."""
        # Create an empty file
        self.coverage_csv.touch()
        with self.assertRaises(DataValidationError) as context:
            load_evaluation_results(self.mock_config)
        self.assertIn("is empty", str(context.exception))

    def test_load_evaluation_results_missing_columns(self):
        """Test that load_evaluation_results raises error if columns missing."""
        df = pd.DataFrame({"bad_col": [1, 2, 3]})
        df.to_csv(self.coverage_csv, index=False)
        with self.assertRaises(DataValidationError) as context:
            load_evaluation_results(self.mock_config)
        self.assertIn("missing required columns", str(context.exception))

    def test_load_evaluation_results_success(self):
        """Test successful loading of valid coverage results."""
        data = {
            "series_id": ["S1", "S2"],
            "model": ["ARIMA", "Prophet"],
            "nominal_level": [0.95, 0.95],
            "empirical_coverage": [0.90, 0.96]
        }
        df = pd.DataFrame(data)
        df.to_csv(self.coverage_csv, index=False)

        loaded_df = load_evaluation_results(self.mock_config)
        self.assertEqual(len(loaded_df), 2)
        self.assertEqual(loaded_df["series_id"].iloc[0], "S1")

    def test_save_conformal_results(self):
        """Test saving conformal results to CSV."""
        results_data = [
            {
                "series_id": "S1",
                "model": "ARIMA",
                "calibration_metric": "absolute_deviation",
                "baseline_value": 0.05,
                "conformal_value": 0.02,
                "improvement_delta": 0.03
            }
        ]
        results_df = pd.DataFrame(results_data)

        output_path = save_conformal_results(results_df, self.mock_config)

        self.assertTrue(os.path.exists(output_path))
        saved_df = pd.read_csv(output_path)
        self.assertEqual(len(saved_df), 1)
        self.assertEqual(saved_df["improvement_delta"].iloc[0], 0.03)


if __name__ == "__main__":
    unittest.main()