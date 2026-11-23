"""Unit tests for statistical correction logic (Bonferroni and FDR).

This module validates the implementation of multiple-comparison correction methods
used in the sensitivity analysis pipeline (Task T029).
"""

import pytest
import numpy as np
from code.eval.metrics import bonferroni_correction, fdr_correction


class TestBonferroniCorrection:
    """Tests for the Bonferroni correction implementation."""

    def test_single_test_no_change(self):
        """When n=1, the p-value should remain unchanged."""
        p_values = [0.05]
        corrected = bonferroni_correction(p_values)
        assert np.isclose(corrected[0], 0.05), "Single test p-value should not change."

    def test_multiple_tests_reduction(self):
        """When n>1, p-values should be multiplied by n (capped at 1.0)."""
        p_values = [0.01, 0.05, 0.1]
        n = len(p_values)
        corrected = bonferroni_correction(p_values)

        # Expected: p * n
        expected = [min(p * n, 1.0) for p in p_values]

        assert len(corrected) == n, "Output length must match input."
        for i, (c, e) in enumerate(zip(corrected, expected)):
            assert np.isclose(c, e), f"Index {i}: expected {e}, got {c}"

    def test_capping_at_one(self):
        """Corrected p-values must not exceed 1.0."""
        p_values = [0.9, 0.8, 0.7]
        corrected = bonferroni_correction(p_values)
        for p in corrected:
            assert 0.0 <= p <= 1.0, f"P-value {p} is out of bounds [0, 1]."

    def test_empty_input(self):
        """Empty list should return empty list."""
        assert bonferroni_correction([]) == []

    def test_very_small_p_values(self):
        """Ensure precision is maintained for very small p-values."""
        p_values = [1e-10, 1e-8, 1e-6]
        n = len(p_values)
        corrected = bonferroni_correction(p_values)
        expected = [p * n for p in p_values]
        for c, e in zip(corrected, expected):
            assert np.isclose(c, e), f"Precision error for small p-value: expected {e}, got {c}"


class TestFDRCorrection:
    """Tests for the False Discovery Rate (Benjamini-Hochberg) correction."""

    def test_single_test_no_change(self):
        """When n=1, the p-value should remain unchanged."""
        p_values = [0.05]
        corrected = fdr_correction(p_values)
        assert np.isclose(corrected[0], 0.05), "Single test p-value should not change."

    def test_multiple_tests_monotonicity(self):
        """FDR corrected p-values must be monotonically non-decreasing with rank."""
        p_values = [0.01, 0.05, 0.1, 0.2]
        corrected = fdr_correction(p_values)

        # Check monotonicity
        for i in range(1, len(corrected)):
            assert corrected[i] >= corrected[i - 1], \
                f"FDR corrected values must be monotonically non-decreasing. Violation at index {i}."

    def test_fdr_vs_bonferroni_less_strict(self):
        """FDR correction should generally yield smaller (less strict) values than Bonferroni."""
        p_values = [0.01, 0.05, 0.1, 0.2]
        bonf = bonferroni_correction(p_values)
        fdr = fdr_correction(p_values)

        # While not strictly guaranteed for every single point in edge cases,
        # the max FDR value should typically be <= max Bonferroni value.
        # We assert that FDR is not *more* strict than Bonferroni on average.
        assert np.mean(fdr) <= np.mean(bonf), "FDR should generally be less strict than Bonferroni."

    def test_empty_input(self):
        """Empty list should return empty list."""
        assert fdr_correction([]) == []

    def test_identical_p_values(self):
        """Test with identical p-values."""
        p_values = [0.05, 0.05, 0.05]
        corrected = fdr_correction(p_values)
        # With identical p-values, the correction logic should still produce a valid monotonic sequence
        assert len(corrected) == 3
        for p in corrected:
            assert 0.0 <= p <= 1.0

    def test_sorting_preserves_rank_order(self):
        """Verify that the correction respects the rank of the original p-values."""
        p_values = [0.1, 0.01, 0.05]
        # The algorithm sorts them: 0.01 (rank 1), 0.05 (rank 2), 0.1 (rank 3)
        # Then applies (p * n) / rank
        # Then ensures monotonicity
        corrected = fdr_correction(p_values)
        assert len(corrected) == 3
        # The smallest original p-value should generally have the smallest corrected value
        # (after unsorting back to original order)
        # Since fdr_correction returns values in the original order:
        # Index 1 (0.01) should be the smallest corrected value
        assert corrected[1] <= corrected[2] <= corrected[0], \
            "Corrected values should reflect the rank order of original p-values."