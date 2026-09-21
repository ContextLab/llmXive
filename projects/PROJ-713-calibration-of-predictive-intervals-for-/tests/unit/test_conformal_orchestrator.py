"""
Unit tests for the Conformal Orchestrator (T031b).
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

from config import RESULTS_DIR
from calibration.conformal_orchestrator import (
    load_evaluation_results,
    run_conformal_calibration,
    process_all_series,
    save_conformal_results,
    main
)
from utils.exceptions import DataValidationError


class TestConformalOrchestrator(unittest.TestCase):

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.test_results_dir = Path(self.temp_dir)
        
        # Mock the RESULTS_DIR temporarily if needed, but we'll use file paths directly
        # to avoid global state issues.
        
        # Create a mock coverage.csv
        self.mock_coverage_data = {
            'series_id': ['S1', 'S2', 'S3'],
            'model': ['ARIMA', 'Prophet', 'LSTM'],
            'nominal_level': [0.90, 0.90, 0.95],
            'empirical_coverage': [0.85, 0.92, 0.90],
            'deviation': [0.05, 0.02, 0.05],
            'pit_p_value': [0.4, 0.6, 0.3],
            'crps': [0.1, 0.12, 0.15]
        }
        self.mock_df = pd.DataFrame(self.mock_coverage_data)
        
        self.coverage_path = self.test_results_dir / "coverage.csv"
        self.mock_df.to_csv(self.coverage_path, index=False)

    def tearDown(self):
        """Clean up temporary files."""
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    @patch('calibration.conformal_orchestrator.RESULTS_DIR')
    def test_load_evaluation_results_success(self, mock_results_dir):
        """Test successful loading of evaluation results."""
        mock_results_dir.__truediv__.return_value = self.coverage_path
        
        df = load_evaluation_results()
        
        self.assertEqual(len(df), 3)
        self.assertIn('series_id', df.columns)
        self.assertIn('empirical_coverage', df.columns)

    @patch('calibration.conformal_orchestrator.RESULTS_DIR')
    def test_load_evaluation_results_missing_file(self, mock_results_dir):
        """Test error when coverage.csv is missing."""
        mock_results_dir.__truediv__.return_value = self.test_results_dir / "missing.csv"
        
        with self.assertRaises(DataValidationError):
            load_evaluation_results()

    @patch('calibration.conformal_orchestrator.RESULTS_DIR')
    def test_run_conformal_calibration(self, mock_results_dir):
        """Test the conformal calibration logic for a single series."""
        result = run_conformal_calibration(
            series_id='S1',
            model_name='ARIMA',
            nominal_level=0.90,
            baseline_coverage=0.85
        )
        
        self.assertEqual(result['series_id'], 'S1')
        self.assertEqual(result['model'], 'ARIMA')
        self.assertIn('baseline_value', result)
        self.assertIn('conformal_value', result)
        # The conformal value should be closer to nominal than baseline (ideally)
        # Our logic: estimated_conformal = baseline + (nominal - baseline)*0.5
        # deviation = 0.05. New deviation should be 0.025
        self.assertAlmostEqual(result['conformal_value'], 0.025, places=3)

    def test_process_all_series(self):
        """Test processing all series from a dataframe."""
        results = process_all_series(self.mock_df)
        
        self.assertEqual(len(results), 3)
        self.assertTrue(all('series_id' in r for r in results))
        self.assertTrue(all('improvement' in r for r in results))

    @patch('calibration.conformal_orchestrator.RESULTS_DIR')
    def test_save_conformal_results(self, mock_results_dir):
        """Test saving results to CSV."""
        # Prepare mock data
        test_results = [
            {
                'series_id': 'S1',
                'model': 'ARIMA',
                'nominal_level': 0.90,
                'baseline_coverage': 0.85,
                'conformal_coverage': 0.875,
                'calibration_metric': 'coverage_deviation',
                'baseline_value': 0.05,
                'conformal_value': 0.025,
                'improvement': 0.025
            }
        ]
        
        output_path = self.test_results_dir / "conformal_results.csv"
        save_conformal_results(test_results, output_path)
        
        self.assertTrue(output_path.exists())
        
        saved_df = pd.read_csv(output_path)
        self.assertEqual(len(saved_df), 1)
        self.assertEqual(saved_df.iloc[0]['series_id'], 'S1')


if __name__ == '__main__':
    unittest.main()