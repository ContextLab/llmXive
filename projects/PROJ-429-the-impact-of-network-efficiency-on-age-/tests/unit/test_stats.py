"""
Unit tests for statistical correction methods (FDR and Bonferroni).
Tests for code/stats/correction.py
"""
import pytest
import numpy as np
from stats.correction import bonferroni_correction, fdr_correction, compare_corrections, apply_correction_to_results
from statsmodels.stats.multitest import multipletests


class TestBonferroniCorrection:
    """Tests for the Bonferroni correction function."""

    def test_bonferroni_basic(self):
        """Test basic Bonferroni correction with known values."""
        p_values = np.array([0.01, 0.05, 0.10, 0.20])
        corrected = bonferroni_correction(p_values)

        # Expected: p * n, capped at 1.0
        # 0.01 * 4 = 0.04
        # 0.05 * 4 = 0.20
        # 0.10 * 4 = 0.40
        # 0.20 * 4 = 0.80
        expected = np.array([0.04, 0.20, 0.40, 0.80])

        np.testing.assert_array_almost_equal(corrected, expected, decimal=10)

    def test_bonferroni_capping(self):
        """Test that corrected p-values are capped at 1.0."""
        p_values = np.array([0.3, 0.4, 0.5])
        corrected = bonferroni_correction(p_values)

        # 0.5 * 3 = 1.5 -> should be capped at 1.0
        assert corrected[2] == 1.0
        assert np.all(corrected <= 1.0)

    def test_bonferroni_empty_input(self):
        """Test handling of empty input."""
        p_values = np.array([])
        corrected = bonferroni_correction(p_values)
        assert len(corrected) == 0

    def test_bonferroni_single_value(self):
        """Test with a single p-value."""
        p_values = np.array([0.05])
        corrected = bonferroni_correction(p_values)
        assert corrected[0] == 0.05  # 0.05 * 1

    def test_bonferroni_zero_values(self):
        """Test with zero p-values."""
        p_values = np.array([0.0, 0.01])
        corrected = bonferroni_correction(p_values)
        assert corrected[0] == 0.0
        assert corrected[1] == 0.01 * 2


class TestFDRCorrection:
    """Tests for the FDR (Benjamini-Hochberg) correction function."""

    def test_fdr_basic(self):
        """Test basic FDR correction."""
        p_values = np.array([0.01, 0.04, 0.08, 0.20])
        corrected = fdr_correction(p_values)

        # Verify it returns an array of the same length
        assert len(corrected) == len(p_values)
        # Verify values are within [0, 1]
        assert np.all(corrected >= 0) and np.all(corrected <= 1)

    def test_fdr_monotonicity(self):
        """Test that FDR corrected p-values are monotonically non-decreasing."""
        p_values = np.array([0.01, 0.04, 0.08, 0.20])
        corrected = fdr_correction(p_values)

        # Check that corrected values are sorted in non-decreasing order
        # (This is a property of the BH procedure after the step-up adjustment)
        assert np.all(np.diff(corrected) >= -1e-10)  # Allow small floating point errors

    def test_fdr_empty_input(self):
        """Test handling of empty input."""
        p_values = np.array([])
        corrected = fdr_correction(p_values)
        assert len(corrected) == 0

    def test_fdr_identical_values(self):
        """Test with identical p-values."""
        p_values = np.array([0.05, 0.05, 0.05])
        corrected = fdr_correction(p_values)
        # All should be adjusted, typically to values >= 0.05
        assert np.all(corrected >= 0.05)


class TestCompareCorrections:
    """Tests for the compare_corrections utility function."""

    def test_compare_returns_dict(self):
        """Test that compare_corrections returns a dictionary."""
        p_values = np.array([0.01, 0.05, 0.10])
        result = compare_corrections(p_values)

        assert isinstance(result, dict)
        assert 'bonferroni' in result
        assert 'fdr' in result
        assert 'raw' in result

    def test_compare_shapes(self):
        """Test that all returned arrays have the same shape."""
        p_values = np.array([0.01, 0.05, 0.10, 0.20])
        result = compare_corrections(p_values)

        assert len(result['bonferroni']) == len(p_values)
        assert len(result['fdr']) == len(p_values)
        assert len(result['raw']) == len(p_values)

    def test_compare_values(self):
        """Test that FDR is less conservative than Bonferroni."""
        p_values = np.array([0.01, 0.02, 0.03, 0.04, 0.05])
        result = compare_corrections(p_values)

        # FDR corrected p-values should generally be smaller (less conservative)
        # than Bonferroni corrected p-values
        assert np.all(result['fdr'] <= result['bonferroni'])


class TestApplyCorrectionToResults:
    """Tests for applying corrections to a results dictionary."""

    def test_apply_to_dict(self):
        """Test applying correction to a dictionary of p-values."""
        results = {
            'metric_a': [0.01, 0.05, 0.10],
            'metric_b': [0.02, 0.06, 0.20]
        }
        corrected_results = apply_correction_to_results(results, method='bonferroni')

        assert 'metric_a' in corrected_results
        assert 'metric_b' in corrected_results
        assert 'metric_a_fdr' in corrected_results
        assert 'metric_b_fdr' in corrected_results

    def test_apply_to_dataframe_like(self):
        """Test applying correction to a list of p-values (simulating a column)."""
        p_values = [0.01, 0.05, 0.10, 0.20]
        results = {'p_values': p_values}

        corrected = apply_correction_to_results(results, method='fdr')

        assert 'p_values_fdr' in corrected
        assert len(corrected['p_values_fdr']) == len(p_values)

    def test_invalid_method(self):
        """Test that an invalid method raises an error."""
        results = {'p': [0.05]}
        with pytest.raises(ValueError):
            apply_correction_to_results(results, method='invalid_method')