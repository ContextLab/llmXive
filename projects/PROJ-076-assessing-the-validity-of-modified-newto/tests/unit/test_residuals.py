"""
Unit tests for residual analysis functions.

Tests cover:
- Residual calculation
- Block-bootstrap permutation test
- Holm-Bonferroni correction
"""

import pytest
import numpy as np
import pandas as pd
from pathlib import Path
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))

from residuals import (
    calculate_residuals,
    block_bootstrap_permutation_test,
    holm_bonferroni_correction
)


class TestCalculateResiduals:
    """Tests for residual calculation function."""

    def test_basic_residual_calculation(self):
        """Test basic observed - predicted calculation."""
        observed = np.array([10.0, 20.0, 30.0])
        predicted = np.array([9.0, 21.0, 29.0])

        residuals, normalized = calculate_residuals(observed, predicted)

        expected_residuals = np.array([1.0, -1.0, 1.0])
        np.testing.assert_array_almost_equal(residuals, expected_residuals)
        assert normalized is None

    def test_residuals_with_uncertainty(self):
        """Test normalized residuals with uncertainty."""
        observed = np.array([10.0, 20.0, 30.0])
        predicted = np.array([9.0, 21.0, 29.0])
        uncertainty = np.array([1.0, 2.0, 0.5])

        residuals, normalized = calculate_residuals(observed, predicted, uncertainty)

        expected_residuals = np.array([1.0, -1.0, 1.0])
        expected_normalized = np.array([1.0, -0.5, 2.0])

        np.testing.assert_array_almost_equal(residuals, expected_residuals)
        np.testing.assert_array_almost_equal(normalized, expected_normalized)

    def test_zero_uncertainty_handling(self):
        """Test handling of zero uncertainty values."""
        observed = np.array([10.0, 20.0, 30.0])
        predicted = np.array([9.0, 21.0, 29.0])
        uncertainty = np.array([0.0, 2.0, 0.5])

        residuals, normalized = calculate_residuals(observed, predicted, uncertainty)

        # Should not raise error, should use small value for zero uncertainty
        assert normalized is not None
        assert not np.any(np.isnan(normalized))


class TestBlockBootstrapPermutationTest:
    """Tests for block-bootstrap permutation test."""

    def test_basic_bootstrap(self):
        """Test basic bootstrap execution."""
        residuals_mond = np.random.normal(0, 1, 100)
        residuals_nfw = np.random.normal(0, 1, 100)

        result = block_bootstrap_permutation_test(
            residuals_mond, residuals_nfw,
            n_bootstrap=100,
            seed=42
        )

        assert 'p_value' in result
        assert 'statistic' in result
        assert 'bootstrap_distribution' in result
        assert 'n_iterations' in result
        assert result['n_iterations'] == 100
        assert 0 <= result['p_value'] <= 1

    def test_mismatched_lengths_raises_error(self):
        """Test that mismatched residual lengths raise an error."""
        residuals_mond = np.random.normal(0, 1, 100)
        residuals_nfw = np.random.normal(0, 1, 50)

        with pytest.raises(ValueError):
            block_bootstrap_permutation_test(
                residuals_mond, residuals_nfw,
                n_bootstrap=100
            )

    def test_deterministic_with_seed(self):
        """Test that results are deterministic with fixed seed."""
        residuals_mond = np.random.normal(0, 1, 100)
        residuals_nfw = np.random.normal(0, 1, 100)

        result1 = block_bootstrap_permutation_test(
            residuals_mond, residuals_nfw,
            n_bootstrap=100,
            seed=42
        )

        result2 = block_bootstrap_permutation_test(
            residuals_mond, residuals_nfw,
            n_bootstrap=100,
            seed=42
        )

        assert result1['p_value'] == result2['p_value']
        assert np.array_equal(
            result1['bootstrap_distribution'],
            result2['bootstrap_distribution']
        )


class TestHolmBonferroniCorrection:
    """Tests for Holm-Bonferroni correction."""

    def test_single_p_value(self):
        """Test correction with a single p-value."""
        p_values = [0.03]
        result = holm_bonferroni_correction(p_values, alpha=0.05)

        assert len(result['corrected_p_values']) == 1
        assert result['corrected_p_values'][0] == 0.03 * 1  # n_tests = 1
        assert result['rejected'][0] == (0.03 < 0.05)

    def test_multiple_p_values(self):
        """Test correction with multiple p-values."""
        p_values = [0.01, 0.03, 0.06, 0.08]
        result = holm_bonferroni_correction(p_values, alpha=0.05)

        assert len(result['corrected_p_values']) == 4
        assert len(result['rejected']) == 4
        assert result['n_tests'] == 4

        # First p-value (0.01) should be rejected (0.01 < 0.05/4 = 0.0125)
        # Second p-value (0.03) should be rejected (0.03 < 0.05/3 = 0.0167) - FALSE
        # Actually: 0.01 < 0.0125 (reject), 0.03 < 0.0167 (no) -> stop
        # So only first should be rejected

        # Check that corrected p-values are monotonically increasing
        corrected = result['corrected_p_values']
        assert all(corrected[i] <= corrected[i+1] for i in range(len(corrected)-1))

    def test_empty_p_values(self):
        """Test with empty p-value list."""
        result = holm_bonferroni_correction([], alpha=0.05)

        assert result['corrected_p_values'] == []
        assert result['rejected'] == []
        assert result['n_tests'] == 0

    def test_all_rejected(self):
        """Test case where all hypotheses are rejected."""
        p_values = [0.001, 0.002, 0.003]
        result = holm_bonferroni_correction(p_values, alpha=0.05)

        # All should be rejected
        assert all(result['rejected'])

    def test_none_rejected(self):
        """Test case where no hypotheses are rejected."""
        p_values = [0.2, 0.3, 0.4]
        result = holm_bonferroni_correction(p_values, alpha=0.05)

        # None should be rejected
        assert not any(result['rejected'])


if __name__ == '__main__':
    pytest.main([__file__, '-v'])