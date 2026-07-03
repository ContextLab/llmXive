"""
Unit tests for code/validate.py focusing on bias test logic and FWER correction.

These tests verify:
1. The regression bias test correctly calculates intercept, slope, and p-values.
2. The Bonferroni correction is applied correctly for multiple hypothesis testing.
3. The validation report generation includes these corrected metrics.
"""
import pytest
import numpy as np
import json
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add project root to path for imports if running standalone
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from validate import (
    regression_bias_test,
    apply_bonferroni_correction,
    generate_validation_report
)


class TestRegressionBiasTest:
    """Tests for the regression bias test logic (y_true ~ y_pred)."""

    def test_bias_test_perfect_prediction(self):
        """Test that perfect predictions yield slope=1, intercept=0."""
        y_true = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        y_pred = np.array([1.0, 2.0, 3.0, 4.0, 5.0])

        result = regression_bias_test(y_true, y_pred)

        # Check that slope is approximately 1 and intercept is approximately 0
        assert np.isclose(result['slope'], 1.0, atol=1e-5)
        assert np.isclose(result['intercept'], 0.0, atol=1e-5)
        # P-value should be non-significant (high) for perfect fit
        assert result['slope_pvalue'] > 0.05

    def test_bias_test_constant_offset(self):
        """Test that a constant offset yields non-zero intercept."""
        y_true = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        y_pred = np.array([1.5, 2.5, 3.5, 4.5, 5.5])  # +0.5 offset

        result = regression_bias_test(y_true, y_pred)

        # Intercept should be approx 0.5, slope approx 1.0
        assert np.isclose(result['intercept'], 0.5, atol=1e-5)
        assert np.isclose(result['slope'], 1.0, atol=1e-5)

    def test_bias_test_sloped_error(self):
        """Test that a scaling error yields non-1 slope."""
        y_true = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        y_pred = np.array([2.0, 4.0, 6.0, 8.0, 10.0])  # 2x scaling

        result = regression_bias_test(y_true, y_pred)

        # Slope should be approx 0.5 (since we regress y_true on y_pred)
        # y_true = slope * y_pred + intercept
        # 1 = slope * 2 => slope = 0.5
        assert np.isclose(result['slope'], 0.5, atol=1e-5)
        assert np.isclose(result['intercept'], 0.0, atol=1e-5)

    def test_bias_test_no_variance_in_pred(self):
        """Test behavior when y_pred has zero variance."""
        y_true = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        y_pred = np.array([1.0, 1.0, 1.0, 1.0, 1.0])

        # Should not crash, but return NaN or raise a specific error handled by caller
        # The implementation should handle this gracefully
        result = regression_bias_test(y_true, y_pred)
        
        # Depending on implementation, slope might be NaN or we might get a specific error
        # For this test, we just ensure it doesn't crash and returns a dict
        assert isinstance(result, dict)
        assert 'slope' in result
        assert 'intercept' in result

    def test_bias_test_random_data(self):
        """Test with random data to ensure p-values are calculated."""
        np.random.seed(42)
        y_true = np.random.randn(100)
        y_pred = y_true * 0.8 + np.random.randn(100) * 0.2

        result = regression_bias_test(y_true, y_pred)

        assert 'slope' in result
        assert 'intercept' in result
        assert 'slope_pvalue' in result
        assert 'intercept_pvalue' in result
        assert isinstance(result['slope'], float)
        assert isinstance(result['intercept'], float)
        assert 0 <= result['slope_pvalue'] <= 1
        assert 0 <= result['intercept_pvalue'] <= 1


class TestBonferroniCorrection:
    """Tests for the Bonferroni correction logic."""

    def test_bonferroni_single_test(self):
        """Test Bonferroni with a single test (no correction)."""
        p_values = [0.05]
        alpha = 0.05
        
        result = apply_bonferroni_correction(p_values, alpha)
        
        assert result['adjusted_alpha'] == 0.05
        assert len(result['significant']) == 1
        assert result['significant'][0] == False  # 0.05 is not < 0.05 (strictly less)
        
    def test_bonferroni_multiple_tests(self):
        """Test Bonferroni with multiple tests."""
        p_values = [0.01, 0.03, 0.06]
        alpha = 0.05
        n_tests = 3
        
        result = apply_bonferroni_correction(p_values, alpha)
        
        expected_adj_alpha = alpha / n_tests  # 0.0167
        assert np.isclose(result['adjusted_alpha'], expected_adj_alpha, atol=1e-5)
        
        # 0.01 < 0.0167 -> significant
        # 0.03 > 0.0167 -> not significant
        # 0.06 > 0.0167 -> not significant
        assert result['significant'] == [True, False, False]

    def test_bonferroni_all_significant(self):
        """Test when all p-values are significant after correction."""
        p_values = [0.001, 0.002, 0.003]
        alpha = 0.05
        
        result = apply_bonferroni_correction(p_values, alpha)
        
        assert all(result['significant'])

    def test_bonferroni_none_significant(self):
        """Test when no p-values are significant after correction."""
        p_values = [0.1, 0.2, 0.3]
        alpha = 0.05
        
        result = apply_bonferroni_correction(p_values, alpha)
        
        assert not any(result['significant'])

    def test_bonferroni_empty_list(self):
        """Test with empty p-value list."""
        p_values = []
        alpha = 0.05
        
        result = apply_bonferroni_correction(p_values, alpha)
        
        assert result['adjusted_alpha'] == alpha  # No division by zero
        assert result['significant'] == []


class TestValidationReportGeneration:
    """Tests for the validation report generation logic."""

    def test_report_structure(self):
        """Test that the validation report has the correct structure."""
        mock_metrics = {
            'r2_mean': 0.85,
            'r2_std': 0.02,
            'rmse_mean': 0.15,
            'mape_mean': 10.5,
            'bias_test': {
                'slope': 0.98,
                'intercept': 0.02,
                'slope_pvalue': 0.12,
                'intercept_pvalue': 0.45
            }
        }
        
        mock_p_values = [mock_metrics['bias_test']['slope_pvalue'], 
                         mock_metrics['bias_test']['intercept_pvalue']]
        mock_alpha = 0.017
        
        # Mock the apply_bonferroni_correction function to avoid actual calculation in this test
        with patch('validate.apply_bonferroni_correction') as mock_bonf:
            mock_bonf.return_value = {
                'adjusted_alpha': 0.017,
                'significant': [False, False]
            }
            
            report = generate_validation_report(mock_metrics, mock_p_values, mock_alpha)
            
            assert 'cross_validation_metrics' in report
            assert 'bias_test_results' in report
            assert 'bonferroni_correction' in report
            assert 'r2_mean' in report['cross_validation_metrics']
            assert 'slope' in report['bias_test_results']
            assert 'adjusted_alpha' in report['bonferroni_correction']

    def test_report_includes_std_threshold(self):
        """Test that the report includes the R2 std threshold check."""
        mock_metrics = {
            'r2_mean': 0.85,
            'r2_std': 0.06,  # Exceeds 0.05 threshold
            'rmse_mean': 0.15,
            'mape_mean': 10.5,
            'bias_test': {
                'slope': 0.98,
                'intercept': 0.02,
                'slope_pvalue': 0.12,
                'intercept_pvalue': 0.45
            }
        }
        
        mock_p_values = [mock_metrics['bias_test']['slope_pvalue'], 
                         mock_metrics['bias_test']['intercept_pvalue']]
        mock_alpha = 0.017
        
        with patch('validate.apply_bonferroni_correction') as mock_bonf:
            mock_bonf.return_value = {
                'adjusted_alpha': 0.017,
                'significant': [False, False]
            }
            
            report = generate_validation_report(mock_metrics, mock_p_values, mock_alpha)
            
            # The report should indicate that the std threshold was exceeded
            assert 'r2_std_threshold_exceeded' in report
            assert report['r2_std_threshold_exceeded'] == True