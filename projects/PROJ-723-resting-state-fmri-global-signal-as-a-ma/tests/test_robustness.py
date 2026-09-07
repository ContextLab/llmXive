"""
Unit tests for User Story 3: Robustness and Sensitivity Analysis.

Specifically implements T033: Verify variance metric correlation is within ±0.05 
of primary SD result.
"""
import os
import sys
import unittest
import json
import tempfile
import shutil
from pathlib import Path

import numpy as np
import pandas as pd

# Add project root to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from robustness import run_variance_metric_analysis, load_cleaned_data_for_robustness
from utils import write_csv, read_csv


class TestVarianceMetricCorrelation(unittest.TestCase):
    """Test that variance metric correlation matches SD correlation within tolerance."""

    def setUp(self):
        """Set up temporary directory and synthetic test data."""
        self.temp_dir = tempfile.mkdtemp()
        self.data_path = os.path.join(self.temp_dir, "cleaned_data.csv")
        
        # Generate synthetic data that mimics the expected structure from T016
        # We need: Subject_ID, Global_Signal_SD, MWQ_Score, Mean_FD, Mean_DVARS
        n_subjects = 100
        np.random.seed(42)
        
        # Create correlated variables to simulate a real relationship
        # Global Signal SD and MWQ should have some correlation
        global_signal_sd = np.random.normal(0.5, 0.1, n_subjects)
        mwq_score = 20 + 15 * global_signal_sd + np.random.normal(0, 2, n_subjects)
        
        # Add some noise and covariates
        mean_fd = np.random.normal(0.2, 0.05, n_subjects)
        mean_dvars = np.random.normal(0.3, 0.08, n_subjects)
        
        subjects = [f"sub-{i:03d}" for i in range(n_subjects)]
        
        df = pd.DataFrame({
            'Subject_ID': subjects,
            'Global_Signal_SD': global_signal_sd,
            'MWQ_Score': mwq_score,
            'Mean_FD': mean_fd,
            'Mean_DVARS': mean_dvars
        })
        
        # Write to temp location
        write_csv(self.data_path, df)

    def tearDown(self):
        """Clean up temporary directory."""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def test_variance_correlation_matches_sd_correlation(self):
        """
        T033: Verify variance metric correlation is within ±0.05 of primary SD result.
        
        This test:
        1. Loads cleaned data
        2. Runs variance metric analysis (Global Signal Variance vs MWQ)
        3. Computes the SD-based correlation (Global Signal SD vs MWQ)
        4. Verifies the difference between correlations is <= 0.05
        """
        # Load the cleaned data
        df = load_cleaned_data_for_robustness(self.data_path)
        
        # Calculate the primary SD correlation (Global_Signal_SD vs MWQ_Score)
        sd_corr = df['Global_Signal_SD'].corr(df['MWQ_Score'])
        
        # Run the variance metric analysis
        # This function computes Global Signal Variance (SD^2) and correlates with MWQ
        variance_results = run_variance_metric_analysis(
            input_path=self.data_path,
            output_path=os.path.join(self.temp_dir, "variance_analysis.json")
        )
        
        # Extract the variance-based correlation
        # The function should return a dict with 'variance_correlation' key
        variance_corr = variance_results.get('variance_correlation')
        
        # Verify the correlation was computed
        self.assertIsNotNone(variance_corr, "Variance correlation should be computed")
        self.assertIsInstance(variance_corr, (int, float), "Correlation should be numeric")
        
        # Calculate the difference
        diff = abs(sd_corr - variance_corr)
        
        # T033 Requirement: Variance metric correlation must be within ±0.05 of SD result
        self.assertLessEqual(
            diff, 
            0.05, 
            f"Variance correlation ({variance_corr:.4f}) differs from SD correlation "
            f"({sd_corr:.4f}) by {diff:.4f}, which exceeds the ±0.05 tolerance."
        )
        
        # Additional sanity checks
        self.assertGreaterEqual(variance_corr, -1.0, "Correlation must be >= -1")
        self.assertLessEqual(variance_corr, 1.0, "Correlation must be <= 1")
        self.assertGreaterEqual(sd_corr, -1.0, "SD correlation must be >= -1")
        self.assertLessEqual(sd_corr, 1.0, "SD correlation must be <= 1")

    def test_variance_metric_analysis_output_structure(self):
        """Verify the variance metric analysis produces expected output structure."""
        output_path = os.path.join(self.temp_dir, "variance_analysis.json")
        
        # Run the analysis
        results = run_variance_metric_analysis(
            input_path=self.data_path,
            output_path=output_path
        )
        
        # Verify output file was created
        self.assertTrue(os.path.exists(output_path), "Output JSON file should be created")
        
        # Verify JSON structure
        with open(output_path, 'r') as f:
            saved_results = json.load(f)
        
        expected_keys = ['variance_correlation', 'sd_correlation', 'n_subjects', 'p_value']
        for key in expected_keys:
            self.assertIn(key, saved_results, f"Output should contain '{key}'")
        
        # Verify results match return value
        self.assertEqual(results['variance_correlation'], saved_results['variance_correlation'])
        self.assertEqual(results['n_subjects'], saved_results['n_subjects'])


if __name__ == '__main__':
    unittest.main()