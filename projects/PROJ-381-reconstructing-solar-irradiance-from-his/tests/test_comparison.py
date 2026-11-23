"""
Unit tests for the comparison module (T026).
"""
import unittest
import pandas as pd
import numpy as np
from pathlib import Path
import json
import tempfile
import os

# We will mock the data loading functions to avoid file I/O in tests
from unittest.mock import patch, MagicMock

from analysis.comparison import (
    calculate_rmse,
    calculate_percentage_error_reduction,
    align_datasets,
    run_comparison_analysis
)

class TestComparisonUtils(unittest.TestCase):
    """Unit tests for utility functions in comparison.py"""

    def test_calculate_rmse(self):
        """Test RMSE calculation"""
        actual = pd.Series([10, 20, 30])
        predicted = pd.Series([11, 19, 31])
        expected_rmse = np.sqrt(np.mean([(10-11)**2, (20-19)**2, (30-31)**2]))
        self.assertAlmostEqual(calculate_rmse(actual, predicted), expected_rmse)

    def test_calculate_percentage_error_reduction(self):
        """Test percentage error reduction calculation"""
        # Original RMSE = 10, New RMSE = 8 -> Reduction = 20%
        self.assertAlmostEqual(
            calculate_percentage_error_reduction(10, 8),
            20.0
        )
        # Edge case: Original RMSE = 0
        self.assertEqual(
            calculate_percentage_error_reduction(0, 5),
            0.0
        )

    def test_align_datasets(self):
        """Test dataset alignment to overlapping period"""
        # Create mock dataframes with date columns
        dates = pd.date_range('2015-01-01', '2017-12-31', freq='MS')
        recon = pd.DataFrame({'date': dates, 'tsi': np.random.rand(len(dates)) * 1360 + 1360})
        base = pd.DataFrame({'date': dates, 'tsi': np.random.rand(len(dates)) * 1360 + 1360})
        cmip = pd.DataFrame({'date': dates, 'tsi': np.random.rand(len(dates)) * 1360 + 1360})
        
        recon_aligned, base_aligned, cmip_aligned = align_datasets(recon, base, cmip, start_year=2016)
        
        # Check that all dates are >= 2016
        self.assertTrue((recon_aligned['date'].dt.year >= 2016).all())
        self.assertTrue((base_aligned['date'].dt.year >= 2016).all())
        self.assertTrue((cmip_aligned['date'].dt.year >= 2016).all())
        
        # Check that all dataframes have the same length (aligned)
        self.assertEqual(len(recon_aligned), len(base_aligned))
        self.assertEqual(len(recon_aligned), len(cmip_aligned))

@patch('analysis.comparison.get_data_path')
@patch('analysis.comparison.ensure_directories')
@patch('analysis.comparison.load_reconstruction_data')
@patch('analysis.comparison.load_baseline_data')
@patch('analysis.comparison.load_cmip_data')
class TestRunComparisonAnalysis(unittest.TestCase):
    """Integration tests for run_comparison_analysis"""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.mock_get_data_path = Path(self.temp_dir)
        self.processed_dir = self.mock_get_data_path / "processed"
        self.processed_dir.mkdir(parents=True, exist_ok=True)
        self.raw_dir = self.mock_get_data_path / "raw"
        self.raw_dir.mkdir(parents=True, exist_ok=True)

    def test_run_comparison_analysis_success(
        self, mock_load_cmip, mock_load_baseline, mock_load_recon, mock_ensure_dirs, mock_get_data_path
    ):
        """Test successful run of comparison analysis with mock data"""
        # Setup mock data
        dates = pd.date_range('2016-01-01', '2020-12-31', freq='MS')
        recon_data = pd.DataFrame({'date': dates, 'tsi': np.random.rand(len(dates)) * 1360 + 1360})
        base_data = pd.DataFrame({'date': dates, 'tsi': np.random.rand(len(dates)) * 1360 + 1360})
        cmip_data = pd.DataFrame({'date': dates, 'tsi': np.random.rand(len(dates)) * 1360 + 1360})
        
        mock_load_recon.return_value = recon_data
        mock_load_baseline.return_value = base_data
        mock_load_cmip.return_value = cmip_data
        mock_get_data_path.return_value = self.mock_get_data_path
        mock_ensure_dirs.return_value = None
        
        # Run the function
        report = run_comparison_analysis()
        
        # Verify report structure
        self.assertIn('overlap_start_year', report)
        self.assertIn('rmse_reconstruction_vs_baseline', report)
        self.assertIn('rmse_reconstruction_vs_cmip', report)
        self.assertIn('percentage_error_reduction', report)
        self.assertIn('methodological_constraints', report)
        
        # Verify file was created
        report_file = self.processed_dir / "comparison_report.json"
        self.assertTrue(report_file.exists())
        
        # Verify report content matches
        with open(report_file) as f:
            saved_report = json.load(f)
        self.assertEqual(report, saved_report)

    def test_run_comparison_analysis_missing_data(
        self, mock_load_cmip, mock_load_baseline, mock_load_recon, mock_ensure_dirs, mock_get_data_path
    ):
        """Test handling of missing data files"""
        mock_load_recon.side_effect = FileNotFoundError("Reconstruction data not found")
        mock_get_data_path.return_value = self.mock_get_data_path
        
        with self.assertRaises(FileNotFoundError):
            run_comparison_analysis()

if __name__ == '__main__':
    unittest.main()