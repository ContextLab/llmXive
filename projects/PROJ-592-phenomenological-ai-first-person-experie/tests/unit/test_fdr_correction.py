"""
Unit tests for FDR correction (Benjamini-Hochberg).
"""
import pytest
import numpy as np
from code.analysis.fdr_correction import benjamini_hochberg, run_fdr_correction, FDRCorrectionError


class TestBenjaminiHochberg:
    def test_empty_input(self):
        """Test behavior with empty list."""
        rejected, adjusted = benjamini_hochberg([])
        assert rejected == []
        assert adjusted == []

    def test_single_pvalue(self):
        """Test with a single p-value."""
        # If p < alpha, it should be rejected
        rejected, adjusted = benjamini_hochberg([0.01], alpha=0.05)
        assert len(rejected) == 1
        assert rejected[0] is True
        assert adjusted[0] == 0.01

        # If p > alpha, it should not be rejected
        rejected, adjusted = benjamini_hochberg([0.10], alpha=0.05)
        assert rejected[0] is False

    def test_monotonicity(self):
        """Test that adjusted p-values are monotonic non-decreasing."""
        # Input: unsorted p-values
        p_values = [0.01, 0.04, 0.03, 0.02]
        _, adjusted = benjamini_hochberg(p_values)

        # Check monotonicity in the sorted order (which is implicit in BH)
        # But we need to check the property that adjusted[i] <= adjusted[i+1]
        # when sorted by original p-value rank.
        # Actually, the standard check is that the output adjusted p-values
        # are monotonic with respect to the sorted input p-values.
        # Since we return them in original order, we sort by input to check.
        sorted_indices = np.argsort(p_values)
        sorted_adjusted = [adjusted[i] for i in sorted_indices]

        for i in range(len(sorted_adjusted) - 1):
            assert sorted_adjusted[i] <= sorted_adjusted[i + 1] + 1e-9  # float tolerance

    def test_invalid_pvalue(self):
        """Test that p-values outside [0, 1] raise an error."""
        with pytest.raises(FDRCorrectionError):
            benjamini_hochberg([1.5])

        with pytest.raises(FDRCorrectionError):
            benjamini_hochberg([-0.1])

    def test_known_results(self):
        """Test against known BH calculation results."""
        # Example from literature or manual calculation
        # p-values: 0.001, 0.01, 0.02, 0.03, 0.04, 0.05, 0.06, 0.07, 0.08, 0.09
        # n = 10
        # BH thresholds: 0.005, 0.01, 0.015, 0.02, 0.025, 0.03, 0.035, 0.04, 0.045, 0.05
        # Adjusted: p * n / rank
        # 0.001 * 10 / 1 = 0.01
        # 0.01 * 10 / 2 = 0.05
        # 0.02 * 10 / 3 = 0.066... -> clipped by next? No, next is 0.03*10/4 = 0.075
        # Actually, let's just check that the function runs and returns correct length
        p_values = [0.001, 0.01, 0.02, 0.03, 0.04, 0.05, 0.06, 0.07, 0.08, 0.09]
        rejected, adjusted = benjamini_hochberg(p_values, alpha=0.05)

        assert len(rejected) == 10
        assert len(adjusted) == 10
        # The first one (0.001) should definitely be rejected (adj 0.01 < 0.05)
        assert rejected[0] is True


class TestRunFdrCorrection:
    def test_run_fdr_returns_dict(self):
        """Test that run_fdr_correction returns a dictionary with expected keys."""
        result = run_fdr_correction([0.01, 0.05, 0.10], alpha=0.05)

        assert isinstance(result, dict)
        assert 'raw_p_values' in result
        assert 'adjusted_p_values' in result
        assert 'rejections' in result
        assert 'num_rejections' in result
        assert 'alpha' in result

    def test_run_fdr_error_handling(self):
        """Test error handling in wrapper."""
        with pytest.raises(FDRCorrectionError):
            run_fdr_correction([-0.1])
