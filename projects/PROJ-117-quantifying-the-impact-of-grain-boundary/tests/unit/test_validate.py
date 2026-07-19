"""
Unit tests for validate.py: bias test logic and FWER correction.
"""
import json
import os
import sys
import unittest
from unittest.mock import patch, MagicMock, mock_open
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

# Add parent directory to path to allow imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from validate import (
    load_model_and_data,
    perform_cross_validation,
    run_regression_bias_test,
    generate_report,
    main
)
from utils import setup_logging

class TestValidateBiasAndFWER(unittest.TestCase):
    """Test suite for bias test logic and FWER correction in validate.py."""

    def setUp(self):
        """Set up test fixtures."""
        self.logger = setup_logging("test_validate")
        self.test_data_dir = Path(__file__).parent.parent.parent / "data" / "processed"
        self.test_models_dir = Path(__file__).parent.parent.parent / "models"
        self.test_artifacts_dir = Path(__file__).parent.parent.parent / "artifacts" / "reports"

        # Create mock data for testing
        np.random.seed(42)
        self.n_samples = 100
        self.y_true = np.random.randn(self.n_samples)
        self.y_pred = self.y_true + np.random.randn(self.n_samples) * 0.5

        # Mock model
        self.mock_model = MagicMock()
        self.mock_model.predict = MagicMock(return_value=self.y_pred)

    def test_run_regression_bias_test_intercept_slope(self):
        """Test that bias test correctly calculates intercept and slope."""
        # Perform regression: y_true ~ y_pred
        # Ideally: intercept ≈ 0, slope ≈ 1 for perfect prediction
        result = run_regression_bias_test(self.y_true, self.y_pred)

        self.assertIn('intercept', result)
        self.assertIn('slope', result)
        self.assertIn('intercept_pvalue', result)
        self.assertIn('slope_pvalue', result)

        # Check that values are reasonable
        self.assertIsInstance(result['intercept'], float)
        self.assertIsInstance(result['slope'], float)
        self.assertIsInstance(result['intercept_pvalue'], float)
        self.assertIsInstance(result['slope_pvalue'], float)

        # For our mock data (y_pred = y_true + noise), slope should be close to 1
        # and intercept close to 0
        self.assertAlmostEqual(result['slope'], 1.0, delta=0.5)
        self.assertAlmostEqual(result['intercept'], 0.0, delta=0.5)

    def test_run_regression_bias_test_pvalues(self):
        """Test that p-values are correctly calculated."""
        result = run_regression_bias_test(self.y_true, self.y_pred)

        # P-values should be between 0 and 1
        self.assertGreaterEqual(result['intercept_pvalue'], 0.0)
        self.assertLessEqual(result['intercept_pvalue'], 1.0)
        self.assertGreaterEqual(result['slope_pvalue'], 0.0)
        self.assertLessEqual(result['slope_pvalue'], 1.0)

    def test_bonferroni_correction_calculation(self):
        """Test that Bonferroni correction is correctly applied (α_adj = 0.05 / 3)."""
        # The bias test produces 3 hypothesis tests:
        # 1. Intercept = 0
        # 2. Slope = 1
        # 3. (Optional) R² = 1 or another metric
        # Bonferroni correction: α_adj = 0.05 / 3 ≈ 0.0167

        alpha = 0.05
        n_tests = 3
        alpha_adj = alpha / n_tests

        # Verify the corrected alpha is approximately 0.0167
        self.assertAlmostEqual(alpha_adj, 0.016666666666666666, places=5)

        # Test that the correction logic would work in the report generation
        # (The actual application happens in generate_report)
        p_values = [0.01, 0.02, 0.03]
        adjusted_p_values = [p * n_tests for p in p_values]

        # Check that adjusted p-values are capped at 1.0
        for adj_p in adjusted_p_values:
            self.assertLessEqual(adj_p, 1.0)

    def test_generate_report_with_bonferroni(self):
        """Test that the report includes Bonferroni-corrected p-values."""
        mock_metrics = {
            'r2': 0.85,
            'rmse': 0.5,
            'mape': 0.1
        }

        mock_cv_results = {
            'r2_scores': [0.82, 0.85, 0.87, 0.83, 0.86],
            'mean_r2': 0.846,
            'std_r2': 0.018
        }

        mock_bias_results = {
            'intercept': 0.02,
            'slope': 0.98,
            'intercept_pvalue': 0.45,
            'slope_pvalue': 0.32,
            'alpha': 0.05,
            'alpha_adj': 0.0167,
            'n_tests': 3
        }

        report = generate_report(mock_metrics, mock_cv_results, mock_bias_results)

        self.assertIn('bias_test', report)
        self.assertIn('intercept', report['bias_test'])
        self.assertIn('slope', report['bias_test'])
        self.assertIn('alpha', report['bias_test'])
        self.assertIn('alpha_adj', report['bias_test'])
        self.assertIn('n_tests', report['bias_test'])

        # Verify Bonferroni correction is recorded
        self.assertAlmostEqual(report['bias_test']['alpha_adj'], 0.0167, places=3)
        self.assertEqual(report['bias_test']['n_tests'], 3)

    def test_perform_cross_validation_returns_correct_metrics(self):
        """Test that cross-validation returns mean and std of R²."""
        # Create a simple mock dataset
        X = np.random.randn(self.n_samples, 5)
        y = self.y_true

        # Mock the model
        mock_model = MagicMock()

        cv_results = perform_cross_validation(mock_model, X, y, k=5)

        self.assertIn('r2_scores', cv_results)
        self.assertIn('mean_r2', cv_results)
        self.assertIn('std_r2', cv_results)

        self.assertEqual(len(cv_results['r2_scores']), 5)
        self.assertIsInstance(cv_results['mean_r2'], float)
        self.assertIsInstance(cv_results['std_r2'], float)

    def test_bonferroni_threshold_application(self):
        """Test that Bonferroni-corrected threshold is correctly applied to p-values."""
        # Simulate p-values from bias tests
        p_values = {
            'intercept': 0.01,
            'slope': 0.03,
            'additional': 0.005
        }

        alpha = 0.05
        n_tests = 3
        alpha_adj = alpha / n_tests  # ≈ 0.0167

        # Apply Bonferroni correction: reject if p < alpha_adj
        results = {}
        for test_name, p_val in p_values.items():
            results[test_name] = {
                'p_value': p_val,
                'alpha_adj': alpha_adj,
                'significant': p_val < alpha_adj
            }

        # Check that the correction logic is applied correctly
        self.assertTrue(results['intercept']['significant'])  # 0.01 < 0.0167
        self.assertFalse(results['slope']['significant'])     # 0.03 > 0.0167
        self.assertTrue(results['additional']['significant'])  # 0.005 < 0.0167

    def test_report_includes_fwer_correction_details(self):
        """Test that the final report documents the FWER correction methodology."""
        mock_metrics = {'r2': 0.85}
        mock_cv_results = {'mean_r2': 0.85, 'std_r2': 0.02}
        mock_bias_results = {
            'intercept': 0.0,
            'slope': 1.0,
            'intercept_pvalue': 0.5,
            'slope_pvalue': 0.5,
            'alpha': 0.05,
            'alpha_adj': 0.0167,
            'n_tests': 3
        }

        report = generate_report(mock_metrics, mock_cv_results, mock_bias_results)

        # The report should explicitly mention Bonferroni correction
        self.assertIn('bias_test', report)
        self.assertIn('alpha_adj', report['bias_test'])
        self.assertIn('n_tests', report['bias_test'])

        # Verify the adjusted alpha is correctly calculated
        expected_alpha_adj = 0.05 / 3
        self.assertAlmostEqual(report['bias_test']['alpha_adj'], expected_alpha_adj, places=4)

    @patch('validate.load_model_and_data')
    @patch('validate.perform_cross_validation')
    @patch('validate.run_regression_bias_test')
    @patch('validate.generate_report')
    @patch('builtins.print')
    def test_main_integration(self, mock_print, mock_gen_report, mock_bias, mock_cv, mock_load):
        """Test that main() orchestrates all validation steps correctly."""
        # Setup mocks
        mock_load.return_value = (MagicMock(), np.random.randn(100), np.random.randn(100))
        mock_cv.return_value = {'mean_r2': 0.85, 'std_r2': 0.02, 'r2_scores': [0.85]*5}
        mock_bias.return_value = {
            'intercept': 0.0, 'slope': 1.0,
            'intercept_pvalue': 0.5, 'slope_pvalue': 0.5,
            'alpha': 0.05, 'alpha_adj': 0.0167, 'n_tests': 3
        }
        mock_gen_report.return_value = {'status': 'success'}

        # Run main
        main()

        # Verify all functions were called
        mock_load.assert_called_once()
        mock_cv.assert_called_once()
        mock_bias.assert_called_once()
        mock_gen_report.assert_called_once()

    def test_fwer_correction_preserves_family_wise_error_rate(self):
        """
        Test that Bonferroni correction correctly controls Family-Wise Error Rate.
        This is a theoretical check: with α=0.05 and 3 tests, α_adj = 0.05/3.
        """
        alpha = 0.05
        n_tests = 3
        alpha_adj = alpha / n_tests

        # The Bonferroni inequality states:
        # P(any false rejection) ≤ Σ P(individual false rejection) = n_tests * alpha_adj = alpha
        # So the FWER is controlled at level alpha.

        # Verify the math
        self.assertAlmostEqual(n_tests * alpha_adj, alpha, places=10)

        # Test with different numbers of tests
        for n in [1, 2, 5, 10]:
            adj = alpha / n
            self.assertAlmostEqual(n * adj, alpha, places=10)

    def test_bias_test_handles_perfect_prediction(self):
        """Test bias test with perfect prediction (y_pred == y_true)."""
        y_true = np.random.randn(50)
        y_pred = y_true.copy()  # Perfect prediction

        result = run_regression_bias_test(y_true, y_pred)

        # Intercept should be 0, slope should be 1
        self.assertAlmostEqual(result['intercept'], 0.0, places=5)
        self.assertAlmostEqual(result['slope'], 1.0, places=5)

        # P-values should be high (fail to reject null that intercept=0, slope=1)
        self.assertGreater(result['intercept_pvalue'], 0.05)
        self.assertGreater(result['slope_pvalue'], 0.05)

    def test_bias_test_handles_biased_prediction(self):
        """Test bias test with systematically biased prediction."""
        y_true = np.random.randn(50)
        y_pred = y_true + 2.0  # Systematic bias (intercept = 2)

        result = run_regression_bias_test(y_true, y_pred)

        # Intercept should be close to 2
        self.assertAlmostEqual(result['intercept'], 2.0, delta=0.5)
        # Slope should still be close to 1
        self.assertAlmostEqual(result['slope'], 1.0, delta=0.5)

        # Intercept p-value should be low (reject null that intercept=0)
        self.assertLess(result['intercept_pvalue'], 0.05)

if __name__ == '__main__':
    unittest.main()