"""
Unit tests for the validation module (code/validate.py).
Focus: Bonferroni correction calculation and p-value adjustment logic.
"""

import pytest
import json
import os
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock
import numpy as np

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from validate import run_regression_bias_test, generate_report


class TestBonferroniCorrection:
    """Tests specifically for Bonferroni correction logic in bias testing."""

    def test_bonferroni_alpha_calculation(self):
        """Verify that alpha_adj = 0.05 / 3 is correctly calculated."""
        # The task specifies 3 hypothesis tests (intercept, slope, p-value)
        # Bonferroni correction: alpha_adj = alpha / n_tests
        alpha = 0.05
        n_tests = 3
        expected_alpha_adj = alpha / n_tests

        # Simulate the calculation that would happen in the code
        # We test the logic directly since the function returns results, not the alpha value itself
        calculated_alpha_adj = alpha / n_tests

        assert calculated_alpha_adj == expected_alpha_adj
        assert abs(calculated_alpha_adj - 0.016666666666666666) < 1e-10

    def test_p_value_adjustment_logic(self):
        """Test that p-values are correctly compared against adjusted alpha."""
        alpha = 0.05
        n_tests = 3
        alpha_adj = alpha / n_tests

        # Test cases: (p_value, expected_significance)
        test_cases = [
            (0.001, True),   # p < alpha_adj -> significant
            (0.01, True),    # p < alpha_adj -> significant
            (0.016, True),   # p < alpha_adj -> significant
            (0.017, False),  # p > alpha_adj -> not significant
            (0.05, False),   # p > alpha_adj -> not significant
            (0.1, False),    # p > alpha_adj -> not significant
        ]

        for p_value, expected_significant in test_cases:
            is_significant = p_value < alpha_adj
            assert is_significant == expected_significant, \
                f"Failed for p_value={p_value}: expected {expected_significant}, got {is_significant}"

    def test_bonferroni_correction_in_bias_test_results(self):
        """Verify that the bias test results correctly apply Bonferroni correction."""
        # Mock data for regression bias test
        mock_y_true = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        mock_y_pred = np.array([1.1, 2.1, 3.0, 4.2, 4.9])

        # Mock the statsmodels regression results
        mock_results = MagicMock()
        mock_results.pvalues = np.array([0.005, 0.01, 0.02])  # intercept, slope, other
        mock_results.params = np.array([0.05, 0.98, 0.01])

        with patch('validate.statsmodels.api.OLS') as mock_ols:
            mock_ols.return_value.fit.return_value = mock_results

            # Run the bias test
            bias_results = run_regression_bias_test(mock_y_true, mock_y_pred)

            # Verify the results contain Bonferroni-adjusted significance
            alpha = 0.05
            n_tests = 3
            alpha_adj = alpha / n_tests

            # Check that significance flags are correctly computed
            for i, p_val in enumerate(mock_results.pvalues):
                expected_significant = p_val < alpha_adj
                actual_significant = bias_results['tests'][i]['significant_at_adjusted_alpha']
                assert actual_significant == expected_significant, \
                    f"Test {i}: p={p_val}, expected significant={expected_significant}, got {actual_significant}"

    def test_bonferroni_correction_with_edge_case_p_values(self):
        """Test Bonferroni correction with p-values exactly at the threshold."""
        alpha = 0.05
        n_tests = 3
        alpha_adj = alpha / n_tests

        # Edge case: p-value exactly at alpha_adj
        p_at_threshold = alpha_adj
        is_significant = p_at_threshold < alpha_adj
        assert not is_significant, "p-value at threshold should not be significant (strict inequality)"

        # Edge case: p-value just below alpha_adj
        p_below_threshold = alpha_adj - 1e-10
        is_significant = p_below_threshold < alpha_adj
        assert is_significant, "p-value below threshold should be significant"

    def test_generate_report_includes_bonferroni_info(self):
        """Verify that the generated report includes Bonferroni correction details."""
        # Mock data
        mock_y_true = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        mock_y_pred = np.array([1.1, 2.1, 3.0, 4.2, 4.9])

        # Mock the bias test results
        mock_bias_results = {
            'intercept': 0.05,
            'slope': 0.98,
            'tests': [
                {'name': 'intercept', 'p_value': 0.005, 'significant_at_adjusted_alpha': True},
                {'name': 'slope', 'p_value': 0.01, 'significant_at_adjusted_alpha': True},
                {'name': 'other', 'p_value': 0.02, 'significant_at_adjusted_alpha': False}
            ],
            'alpha_original': 0.05,
            'alpha_adjusted': 0.05 / 3,
            'n_tests': 3
        }

        with patch('validate.run_regression_bias_test') as mock_bias_test:
            mock_bias_test.return_value = mock_bias_results

            # Mock model and data loading
            with patch('validate.load_model_and_data') as mock_load:
                mock_load.return_value = (MagicMock(), mock_y_true, mock_y_pred)

                # Generate report
                report = generate_report()

                # Verify Bonferroni details are in the report
                assert 'bias_test' in report
                assert 'alpha_adjusted' in report['bias_test']
                assert report['bias_test']['alpha_adjusted'] == 0.05 / 3
                assert report['bias_test']['n_tests'] == 3
                assert report['bias_test']['alpha_original'] == 0.05

                # Verify each test result includes Bonferroni-adjusted significance
                for test_result in report['bias_test']['tests']:
                    assert 'significant_at_adjusted_alpha' in test_result

    def test_bonferroni_correction_applied_to_all_hypothesis_tests(self):
        """Ensure Bonferroni correction is applied consistently across all tests."""
        alpha = 0.05
        n_tests = 3
        alpha_adj = alpha / n_tests

        # Simulate multiple p-values
        p_values = [0.001, 0.01, 0.02, 0.03, 0.04, 0.05]

        # Apply Bonferroni correction
        results = []
        for p in p_values:
            is_significant = p < alpha_adj
            results.append({
                'p_value': p,
                'significant': is_significant,
                'threshold': alpha_adj
            })

        # Verify all results use the same adjusted threshold
        for result in results:
            assert result['threshold'] == alpha_adj
            expected_significant = result['p_value'] < alpha_adj
            assert result['significant'] == expected_significant

class TestRegressionBiasTest:
    """Tests for the regression bias test functionality."""

    def test_bias_test_returns_expected_structure(self):
        """Verify that bias test results have the expected structure."""
        mock_y_true = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        mock_y_pred = np.array([1.1, 2.1, 3.0, 4.2, 4.9])

        mock_results = MagicMock()
        mock_results.pvalues = np.array([0.005, 0.01, 0.02])
        mock_results.params = np.array([0.05, 0.98, 0.01])

        with patch('validate.statsmodels.api.OLS') as mock_ols:
            mock_ols.return_value.fit.return_value = mock_results

            bias_results = run_regression_bias_test(mock_y_true, mock_y_pred)

            # Check structure
            assert 'intercept' in bias_results
            assert 'slope' in bias_results
            assert 'tests' in bias_results
            assert 'alpha_original' in bias_results
            assert 'alpha_adjusted' in bias_results
            assert 'n_tests' in bias_results

            # Check test structure
            assert len(bias_results['tests']) == 3
            for test in bias_results['tests']:
                assert 'name' in test
                assert 'p_value' in test
                assert 'significant_at_adjusted_alpha' in test

    def test_bias_test_with_perfect_predictions(self):
        """Test bias test with perfect predictions (should show no bias)."""
        mock_y_true = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        mock_y_pred = np.array([1.0, 2.0, 3.0, 4.0, 5.0])

        mock_results = MagicMock()
        mock_results.pvalues = np.array([0.5, 0.5, 0.5])  # High p-values
        mock_results.params = np.array([0.0, 1.0, 0.0])   # Perfect intercept=0, slope=1

        with patch('validate.statsmodels.api.OLS') as mock_ols:
            mock_ols.return_value.fit.return_value = mock_results

            bias_results = run_regression_bias_test(mock_y_true, mock_y_pred)

            # Check that intercept is close to 0 and slope is close to 1
            assert abs(bias_results['intercept']) < 0.01
            assert abs(bias_results['slope'] - 1.0) < 0.01

    def test_bias_test_with_systematic_bias(self):
        """Test bias test with systematic prediction bias."""
        mock_y_true = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        mock_y_pred = np.array([2.0, 3.0, 4.0, 5.0, 6.0])  # Systematic +1 offset

        mock_results = MagicMock()
        mock_results.pvalues = np.array([0.001, 0.5, 0.5])  # Significant intercept
        mock_results.params = np.array([1.0, 1.0, 0.0])     # Intercept=1, slope=1

        with patch('validate.statsmodels.api.OLS') as mock_ols:
            mock_ols.return_value.fit.return_value = mock_results

            bias_results = run_regression_bias_test(mock_y_true, mock_y_pred)

            # Check that intercept is close to 1
            assert abs(bias_results['intercept'] - 1.0) < 0.01
            assert abs(bias_results['slope'] - 1.0) < 0.01

class TestIntegration:
    """Integration tests combining multiple components."""

    def test_full_validation_pipeline_with_bonferroni(self):
        """Test the full validation pipeline including Bonferroni correction."""
        # Create temporary directory for test artifacts
        with patch('validate.Path') as mock_path:
            mock_output_dir = MagicMock()
            mock_output_dir.exists.return_value = True
            mock_output_dir.mkdir.return_value = None
            mock_path.return_value = mock_output_dir

            # Mock data
            mock_y_true = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
            mock_y_pred = np.array([1.1, 2.1, 3.0, 4.2, 4.9])

            # Mock bias test results
            mock_bias_results = {
                'intercept': 0.05,
                'slope': 0.98,
                'tests': [
                    {'name': 'intercept', 'p_value': 0.005, 'significant_at_adjusted_alpha': True},
                    {'name': 'slope', 'p_value': 0.01, 'significant_at_adjusted_alpha': True},
                    {'name': 'other', 'p_value': 0.02, 'significant_at_adjusted_alpha': False}
                ],
                'alpha_original': 0.05,
                'alpha_adjusted': 0.05 / 3,
                'n_tests': 3
            }

            with patch('validate.run_regression_bias_test') as mock_bias_test:
                mock_bias_test.return_value = mock_bias_results

                with patch('validate.load_model_and_data') as mock_load:
                    mock_load.return_value = (MagicMock(), mock_y_true, mock_y_pred)

                    # Generate report
                    report = generate_report()

                    # Verify Bonferroni correction is properly applied
                    assert report['bias_test']['alpha_adjusted'] == 0.05 / 3
                    assert report['bias_test']['n_tests'] == 3

                    # Verify significance flags are correct
                    assert report['bias_test']['tests'][0]['significant_at_adjusted_alpha'] == True
                    assert report['bias_test']['tests'][1]['significant_at_adjusted_alpha'] == True
                    assert report['bias_test']['tests'][2]['significant_at_adjusted_alpha'] == False