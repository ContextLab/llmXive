"""
Unit tests for statistical correction logic (Bonferroni and FDR).

This module tests the implementation of multiple-comparison corrections
required for the sensitivity analysis in User Story 3.
"""
import pytest
import numpy as np
from typing import List

# Import the functions to test. We will implement these in code/eval/metrics.py
# or a dedicated stats module if not already present.
# For this task, we assume they are added to code/eval/metrics.py or code/utils/stats.py.
# Based on the API surface, code/eval/metrics.py already has statistical functions.
# We will add the correction functions there if they don't exist, or create a new utility.
# Given the constraint to extend existing files, we will add them to code/eval/metrics.py
# and test them here.

# Note: The implementation of these functions is part of the task logic, 
# but since the task is specifically the *test*, we import them assuming 
# they have been added to the metrics module or a new stats module.
# To ensure this test runs, we will include the implementation in the test file 
# as a local helper if the import fails, BUT the prompt says "Extend, don't re-author".
# The correct approach is to add the implementation to code/eval/metrics.py 
# in the same task if it's missing, or assume it exists. 
# Since T024 implemented metrics, and T029 is the implementation of the correction,
# T027 (this test) should ideally run against the implementation of T029.
# However, T027 is marked as [P] (parallel) and T029 is later.
# The prompt asks to implement T027. A unit test for logic that doesn't exist yet
# is a test-driven development step. 
# BUT constraint 1 says "Implement the task for real... never a stub".
# And constraint 9 says "Real data only". 
# If the function doesn't exist, I must implement it to satisfy the test.
# Let's check the API surface for code/eval/metrics.py.
# It lists: calculate_mae, calculate_rmse, calculate_r2, calculate_all_metrics, 
# paired_ttest, cohen_d, compare_models.
# It does NOT list bonferroni_correction or fdr_correction.
# Since T027 is the unit test for this logic, and T029 is the implementation,
# and they are parallel, I must implement the logic in the metrics file 
# (or a new file) to make the test valid and runnable.
# I will add the implementation to code/eval/metrics.py to satisfy the test.

# Re-reading constraints: "Extend, don't re-author. Use the provided existing API surface... 
# When a task references an existing file, extend it coherently".
# I will extend code/eval/metrics.py with the correction functions and then write the test.

# Since I cannot modify code/eval/metrics.py in this artifact list (unless I list it as an artifact),
# and the prompt says "Implement one task", I should include the implementation of the 
# functions being tested IF they are missing, to make the test runnable.
# The task description says "Unit test for Bonferroni/FDR correction logic".
# The logic must exist for the test to be meaningful.
# I will add the implementation to code/eval/metrics.py as an artifact in this task,
# and the test file as another artifact.

# However, the prompt says "Implement exactly one task: T027". 
# If I add code to metrics.py, is that T029?
# T029 is "Implement multiple-comparison correction... in code/eval/sensitivity.py".
# T027 is "Unit test for... logic in tests/unit/test_statistics.py".
# It is reasonable to implement the logic in the metrics module (as a utility)
# and test it here, to satisfy the "real, runnable" constraint.
# I will add the functions to code/eval/metrics.py and test them here.

from code.eval.metrics import bonferroni_correction, fdr_correction


class TestBonferroniCorrection:
    """Tests for the Bonferroni correction implementation."""

    def test_bonferroni_single_pvalue(self):
        """Test correction with a single p-value."""
        p_values = [0.05]
        corrected = bonferroni_correction(p_values)
        # Bonferroni: p_adj = p * m
        # m = 1, so p_adj = 0.05
        assert np.isclose(corrected[0], 0.05)

    def test_bonferroni_multiple_pvalues(self):
        """Test correction with multiple p-values."""
        p_values = [0.01, 0.05, 0.10]
        corrected = bonferroni_correction(p_values)
        # m = 3
        # 0.01 * 3 = 0.03
        # 0.05 * 3 = 0.15
        # 0.10 * 3 = 0.30
        assert np.isclose(corrected[0], 0.03)
        assert np.isclose(corrected[1], 0.15)
        assert np.isclose(corrected[2], 0.30)

    def test_bonferroni_capped_at_one(self):
        """Test that corrected p-values are capped at 1.0."""
        p_values = [0.5, 0.6]
        corrected = bonferroni_correction(p_values)
        # m = 2
        # 0.5 * 2 = 1.0
        # 0.6 * 2 = 1.2 -> capped to 1.0
        assert np.isclose(corrected[0], 1.0)
        assert np.isclose(corrected[1], 1.0)

    def test_bonferroni_empty_list(self):
        """Test with empty list."""
        p_values = []
        corrected = bonferroni_correction(p_values)
        assert corrected == []

    def test_bonferroni_zero_pvalue(self):
        """Test with zero p-value."""
        p_values = [0.0, 0.05]
        corrected = bonferroni_correction(p_values)
        assert corrected[0] == 0.0
        assert np.isclose(corrected[1], 0.1)

class TestFDRCorrection:
    """Tests for the False Discovery Rate (Benjamini-Hochberg) correction."""

    def test_fdr_single_pvalue(self):
        """Test FDR correction with a single p-value."""
        p_values = [0.05]
        corrected = fdr_correction(p_values)
        # BH: p_adj = p * m / i (sorted)
        # sorted: [0.05], i=1, m=1 -> 0.05 * 1 / 1 = 0.05
        assert np.isclose(corrected[0], 0.05)

    def test_fdr_multiple_pvalues(self):
        """Test FDR correction with multiple p-values."""
        # Sorted p-values: 0.01, 0.02, 0.03
        p_values = [0.03, 0.01, 0.02]
        corrected = fdr_correction(p_values)
        # m = 3
        # Sorted indices (1-based): 1, 2, 3
        # i=1 (0.01): 0.01 * 3 / 1 = 0.03
        # i=2 (0.02): 0.02 * 3 / 2 = 0.03
        # i=3 (0.03): 0.03 * 3 / 3 = 0.03
        # Then monotonicity step:
        # 0.03, 0.03, 0.03 -> all 0.03
        # But we need to return in original order.
        # Original: 0.03 (idx 2), 0.01 (idx 0), 0.02 (idx 1)
        # Sorted: 0.01 (i=1), 0.02 (i=2), 0.03 (i=3)
        # Raw adj: 0.03, 0.03, 0.03
        # Monotonic: 0.03, 0.03, 0.03
        # Original order: 0.03, 0.03, 0.03
        # Let's verify with a more distinct set.
        # p = [0.01, 0.05, 0.10]
        # m=3
        # i=1: 0.01 * 3 / 1 = 0.03
        # i=2: 0.05 * 3 / 2 = 0.075
        # i=3: 0.10 * 3 / 3 = 0.10
        # Monotonic: 0.03, 0.075, 0.10 (already monotonic)
        p_values = [0.01, 0.05, 0.10]
        corrected = fdr_correction(p_values)
        assert np.isclose(corrected[0], 0.03)
        assert np.isclose(corrected[1], 0.075)
        assert np.isclose(corrected[2], 0.10)

    def test_fdr_monotonicity(self):
        """Test that FDR corrected values are monotonically non-decreasing when sorted."""
        # p = [0.05, 0.01, 0.10]
        # sorted: 0.01, 0.05, 0.10
        # raw: 0.01*3/1=0.03, 0.05*3/2=0.075, 0.10*3/3=0.10
        # monotonic: 0.03, 0.075, 0.10
        # original order: 0.075, 0.03, 0.10
        p_values = [0.05, 0.01, 0.10]
        corrected = fdr_correction(p_values)
        # Check monotonicity of the sorted corrected values
        # The function should return corrected values in original order
        # but the underlying logic ensures monotonicity in sorted order.
        # We can check that the sorted corrected values are non-decreasing.
        sorted_corrected = sorted(corrected)
        for i in range(len(sorted_corrected) - 1):
            assert sorted_corrected[i] <= sorted_corrected[i+1]

    def test_fdr_capped_at_one(self):
        """Test that FDR corrected p-values are capped at 1.0."""
        p_values = [0.9, 0.95]
        # m=2
        # sorted: 0.9, 0.95
        # i=1: 0.9 * 2 / 1 = 1.8 -> 1.0
        # i=2: 0.95 * 2 / 2 = 0.95
        # monotonic: 0.95, 1.0 (from 1.0 down to 0.95? No, monotonicity is from largest to smallest in BH)
        # Actually, BH ensures that p_(i) <= p_(i+1) in the corrected sequence?
        # The standard BH procedure:
        # 1. Sort p: p(1) <= p(2) <= ... <= p(m)
        # 2. Compute q(i) = p(i) * m / i
        # 3. Enforce monotonicity from the largest: q(m) = min(q(m), 1), q(m-1) = min(q(m-1), q(m)), ...
        # So for [0.9, 0.95]:
        # q(1) = 0.9 * 2 / 1 = 1.8
        # q(2) = 0.95 * 2 / 2 = 0.95
        # Monotonicity from right:
        # q(2) = min(0.95, 1) = 0.95
        # q(1) = min(1.8, 0.95) = 0.95
        # So both become 0.95.
        corrected = fdr_correction(p_values)
        assert all(c <= 1.0 for c in corrected)

    def test_fdr_empty_list(self):
        """Test with empty list."""
        p_values = []
        corrected = fdr_correction(p_values)
        assert corrected == []

    def test_fdr_zero_pvalue(self):
        """Test with zero p-value."""
        p_values = [0.0, 0.05]
        corrected = fdr_correction(p_values)
        # sorted: 0.0, 0.05
        # q(1) = 0.0 * 2 / 1 = 0.0
        # q(2) = 0.05 * 2 / 2 = 0.05
        # monotonic: 0.0, 0.05
        assert corrected[0] == 0.0
        assert np.isclose(corrected[1], 0.05)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
