"""
Tests for T024: Non-linear interaction analysis.
"""
import os
import sys
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock

import numpy as np
import pandas as pd

# Add project root to path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from code import config
from code import utils
from code.utils import stats_helpers

# Import the module under test
from code.nonlinear_analysis import load_features, prepare_polynomial_features, fit_models, main

class TestNonLinearAnalysis(unittest.TestCase):

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.data_path = Path(self.temp_dir.name) / "data" / "processed"
        self.data_path.mkdir(parents=True)
        
        # Mock the config get_path to point to our temp dir
        self.original_get_path = config.get_path
        def mock_get_path(subdir, filename):
            return str(self.data_path / filename)
        config.get_path = mock_get_path

        # Create a dummy features.csv
        self.dummy_data = pd.DataFrame({
            'participant_id': [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
            'median_rt': [300, 310, 290, 350, 320, 280, 330, 340, 295, 305],
            'alpha_rel': [0.1, 0.12, 0.09, 0.15, 0.11, 0.08, 0.13, 0.14, 0.1, 0.11],
            'beta_rel': [0.2, 0.22, 0.18, 0.25, 0.21, 0.17, 0.23, 0.24, 0.19, 0.21]
        })
        self.dummy_data.to_csv(self.data_path / "features.csv", index=False)

    def tearDown(self):
        """Clean up test fixtures."""
        config.get_path = self.original_get_path
        self.temp_dir.cleanup()

    def test_load_features(self):
        """Test loading features from CSV."""
        df = load_features()
        self.assertEqual(len(df), 10)
        self.assertIn('alpha_rel', df.columns)
        self.assertIn('beta_rel', df.columns)
        self.assertIn('median_rt', df.columns)

    def test_prepare_polynomial_features(self):
        """Test polynomial feature creation."""
        df = pd.DataFrame({
            'alpha_rel': [0.5],
            'beta_rel': [0.6],
            'median_rt': [300]
        })
        df_poly = prepare_polynomial_features(df)
        
        self.assertAlmostEqual(df_poly['alpha_sq'].iloc[0], 0.25, places=5)
        self.assertAlmostEqual(df_poly['beta_sq'].iloc[0], 0.36, places=5)
        self.assertAlmostEqual(df_poly['alpha_beta_interact'].iloc[0], 0.30, places=5)

    def test_fit_models(self):
        """Test model fitting and F-test calculation."""
        df = prepare_polynomial_features(self.dummy_data)
        results = fit_models(df)
        
        # Check structure
        self.assertIn('reduced_model', results)
        self.assertIn('full_model', results)
        self.assertIn('f_test', results)
        
        # Check numeric types
        self.assertIsInstance(results['reduced_model']['r_squared'], float)
        self.assertIsInstance(results['f_test']['f_statistic'], float)
        self.assertIsInstance(results['f_test']['p_value'], float)
        
        # Check degrees of freedom logic
        # Reduced: 3 params (intercept, alpha, beta)
        # Full: 6 params (intercept, alpha, beta, alpha^2, beta^2, interaction)
        # N = 10
        # df_res_reduced = 10 - 3 = 7
        # df_res_full = 10 - 6 = 4
        self.assertEqual(results['reduced_model']['degrees_of_freedom_residual'], 7)
        self.assertEqual(results['full_model']['degrees_of_freedom_residual'], 4)
        self.assertEqual(results['f_test']['numerator_df'], 3) # 6 - 3
        self.assertEqual(results['f_test']['denominator_df'], 4)

    def test_main_integration(self):
        """Test the main function execution."""
        output_file = self.data_path / "test_results.json"
        
        # Mock sys.argv to simulate CLI call
        with patch('sys.argv', ['code/12_nonlinear_analysis.py', '--output', str(output_file)]):
            main()
        
        self.assertTrue(output_file.exists())
        
        with open(output_file, 'r') as f:
            data = json.load(f)
        
        self.assertIn('f_test', data)
        self.assertIn('significant_at_0.05', data['f_test'])

    def test_insufficient_data(self):
        """Test that fitting fails gracefully with too few samples."""
        # Create a tiny dataset: 3 samples, but full model needs 6 params
        tiny_df = pd.DataFrame({
            'participant_id': [1, 2, 3],
            'median_rt': [300, 310, 290],
            'alpha_rel': [0.1, 0.12, 0.09],
            'beta_rel': [0.2, 0.22, 0.18]
        })
        # Add poly features
        tiny_df['alpha_sq'] = tiny_df['alpha_rel'] ** 2
        tiny_df['beta_sq'] = tiny_df['beta_rel'] ** 2
        tiny_df['alpha_beta_interact'] = tiny_df['alpha_rel'] * tiny_df['beta_rel']
        
        # This should raise ValueError because df_res_full would be 3 - 6 = -3
        with self.assertRaises(ValueError):
            fit_models(tiny_df)

if __name__ == '__main__':
    unittest.main()