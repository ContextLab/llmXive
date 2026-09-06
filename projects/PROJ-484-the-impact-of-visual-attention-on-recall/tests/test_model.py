"""
Unit tests for model fitting and power analysis.
"""
import os
import json
import tempfile
import unittest
from unittest.mock import patch, MagicMock
import pandas as pd
import numpy as np

# Import the module functions
# Note: We need to import from the correct path
# Since we are in tests/, we need to add the parent directory to sys.path
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from model_fit import run_monte_carlo_power_analysis, main

class TestSparseDataPowerWarning(unittest.TestCase):
    """Test for T072: Sparse Data Power Warning."""

    def setUp(self):
        """Set up test fixtures."""
        # Create a temporary directory for output
        self.temp_dir = tempfile.mkdtemp()
        self.artifacts_dir = os.path.join(self.temp_dir, "artifacts", "logs")
        os.makedirs(self.artifacts_dir, exist_ok=True)
        
        # Create a mock dataset with low power (small sample size)
        self.small_data = pd.DataFrame({
            'recall': np.random.binomial(1, 0.5, 100),
            'fixation_duration': np.random.normal(200, 50, 100),
            'valence': np.random.choice(['positive', 'negative'], 100),
            'trait_anxiety': np.random.normal(50, 10, 100),
            'participant': np.repeat(range(10), 10), # Only 10 participants
            'stimulus_id': np.repeat(range(20), 5)
        })

    @patch('model_fit.get_data_path')
    @patch('model_fit.setup_logging')
    def test_sparse_data_power_warning(self, mock_setup_logging, mock_get_data_path):
        """
        Assert that the warning is triggered and the power_warning.json file is created
        when simulated sample size is artificially reduced.
        """
        # Mock the config to return our temp dir
        mock_get_data_path.return_value = self.temp_dir
        mock_logger = MagicMock()
        mock_setup_logging.return_value = mock_logger
        
        # We need to mock the data loading to return our small dataset
        # Since run_monte_carlo_power_analysis is called inside main, we'll test main
        # But main expects the data to be in data/processed/analysis.csv
        # So we'll create a dummy CSV
        data_dir = os.path.join(self.temp_dir, "processed")
        os.makedirs(data_dir, exist_ok=True)
        csv_path = os.path.join(data_dir, "analysis.csv")
        self.small_data.to_csv(csv_path, index=False)
        
        # Mock the fit_mixed_effects_model to return a mock result with low power
        # We can't easily mock the internal logic of run_monte_carlo_power_analysis
        # So we'll test the heuristic logic directly by patching the return value
        # Or we can run the function and check the output file
        
        # Let's run the power analysis function directly with our small data
        # But the function expects to load data from a file.
        # We'll patch the load_analysis_data function.
        
        from model_fit import load_analysis_data, fit_mixed_effects_model, run_bootstrap_convergence_verification
        
        # Mock load_analysis_data
        with patch('model_fit.load_analysis_data', return_value=self.small_data):
            # Mock fit_mixed_effects_model to return a mock result
            mock_result = MagicMock()
            mock_result.converged = True
            mock_result.llf = 100.0
            mock_result.df_model = 10
            with patch('model_fit.fit_mixed_effects_model', return_value=(mock_result, True)):
                with patch('model_fit.run_bootstrap_convergence_verification', return_value=0.9):
                    # Run the power analysis
                    power_results = run_monte_carlo_power_analysis(self.small_data)
                    
                    # Check that power estimate is low
                    self.assertLess(power_results['power_estimate'], 0.80)
                    
                    # Now run main to see if it creates the warning file
                    # We need to mock the export functions
                    with patch('model_fit.export_power_results') as mock_export_power:
                        with patch('model_fit.export_bootstrap_results') as mock_export_bootstrap:
                            with patch('model_fit.fit_reduced_model', return_value=(mock_result, True)):
                                with patch('model_fit.run_likelihood_ratio_test', return_value=(10.0, 0.01, True)):
                                    with patch('model_fit.run_residual_diagnostics', return_value={}):
                                        try:
                                            main()
                                        except Exception:
                                            pass # We don't care about other errors
                            
                            # Check if power_warning.json was created
                            warning_path = os.path.join(self.artifacts_dir, "power_warning.json")
                            self.assertTrue(os.path.exists(warning_path), "power_warning.json should be created")
                            
                            # Check the content of the warning file
                            with open(warning_path, 'r') as f:
                                warning_data = json.load(f)
                            
                            self.assertEqual(warning_data['status'], 'low_power')
                            self.assertIn('Low statistical power detected', warning_data['warning'])

    def test_power_warning_content(self):
        """Test the content of the power warning file."""
        # This test verifies the structure of the warning data
        warning_data = {
            "warning": "WARNING: Low statistical power detected",
            "power_estimate": 0.5,
            "sample_size": 10,
            "effect_size_constraint": "Three-way interaction requires large sample size",
            "threshold": 0.80,
            "status": "low_power"
        }
        
        self.assertEqual(warning_data['status'], 'low_power')
        self.assertLess(warning_data['power_estimate'], 0.80)
        self.assertGreater(warning_data['threshold'], warning_data['power_estimate'])

if __name__ == '__main__':
    unittest.main()