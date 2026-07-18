"""
Unit test for paired t-test calculation (p-value, t-stat, Cohen's d).
Implements T027: [US3] Unit test for paired t-test calculation.

This test verifies the statistical analysis logic used in Phase 5 (User Story 3)
to compare the complex-valued model against the real-valued baseline.
"""
import pytest
import math
import sys
import os

# Add the project code directory to the path so we can import analysis modules
# The task expects the test to be runnable from the project root.
code_path = os.path.join(os.path.dirname(__file__), '..', '..', 'code')
if code_path not in sys.path:
    sys.path.insert(0, code_path)

from analysis.stats_test import paired_t_test, calculate_cohens_d


class TestPairedTTest:
    """Tests for the paired t-test implementation."""

    def test_identical_scores(self):
        """If scores are identical, t-stat should be 0 and p-value should be 1."""
        baseline = [0.80, 0.81, 0.79, 0.82]
        quantum = [0.80, 0.81, 0.79, 0.82]

        result = paired_t_test(baseline, quantum)

        assert math.isclose(result['t_stat'], 0.0, abs_tol=1e-6)
        assert math.isclose(result['p_value'], 1.0, abs_tol=1e-6)
        assert result['n'] == 4
        assert result['mean_diff'] == 0.0

    def test_significant_improvement(self):
        """Test case where quantum model is significantly better."""
        # Simulate baseline around 0.70, quantum around 0.80 with low variance
        baseline = [0.70, 0.71, 0.69, 0.70, 0.71]
        quantum = [0.80, 0.81, 0.79, 0.80, 0.81]

        result = paired_t_test(baseline, quantum)

        assert result['t_stat'] > 0  # Positive t-stat indicates improvement
        assert result['p_value'] < 0.05  # Significant at alpha=0.05
        assert result['mean_diff'] > 0.05  # Mean difference should be around 0.1

    def test_no_significant_difference(self):
        """Test case where difference is small and variance is high."""
        # High variance, small mean difference
        baseline = [0.70, 0.90, 0.60, 0.80]
        quantum = [0.72, 0.88, 0.62, 0.78]

        result = paired_t_test(baseline, quantum)

        # t-stat should be small
        assert abs(result['t_stat']) < 2.0
        # p-value should be > 0.05 (not significant)
        assert result['p_value'] > 0.05
        assert math.isclose(result['mean_diff'], 0.02, abs_tol=1e-2)

    def test_cohens_d_calculation(self):
        """Verify Cohen's d is calculated correctly."""
        # Effect size calculation: mean_diff / std_diff
        # If mean_diff = 0.1 and std_diff = 0.05, d = 2.0
        baseline = [0.5, 0.5, 0.5, 0.5]
        quantum = [0.6, 0.6, 0.6, 0.6]

        result = paired_t_test(baseline, quantum)

        # Standard deviation of differences [0.1, 0.1, 0.1, 0.1] is 0.0
        # This is a degenerate case, so we test a non-degenerate one
        baseline = [0.5, 0.6, 0.5, 0.6]
        quantum = [0.6, 0.7, 0.6, 0.7] # diffs: 0.1, 0.1, 0.1, 0.1 -> still 0 std

        # Let's try varying diffs
        baseline = [0.5, 0.5, 0.5, 0.5]
        quantum = [0.6, 0.7, 0.5, 0.6] # diffs: 0.1, 0.2, 0.0, 0.1
        # mean_diff = 0.1
        # variance = ((0)^2 + (0.1)^2 + (-0.1)^2 + (0)^2) / 3 = 0.02
        # std = sqrt(0.02) ≈ 0.1414
        # d = 0.1 / 0.1414 ≈ 0.707

        result = paired_t_test(baseline, quantum)
        
        # Check that Cohen's d is in the output
        assert 'cohen_d' in result
        assert result['cohen_d'] > 0.5
        assert result['cohen_d'] < 0.8

    def test_negative_improvement(self):
        """Test case where quantum model performs worse."""
        baseline = [0.85, 0.86, 0.84, 0.85]
        quantum = [0.75, 0.76, 0.74, 0.75]

        result = paired_t_test(baseline, quantum)

        assert result['t_stat'] < 0  # Negative t-stat
        assert result['p_value'] < 0.05  # Significant drop
        assert result['mean_diff'] < 0


class TestCohensDFunction:
    """Specific tests for the calculate_cohens_d helper."""

    def test_cohens_d_basic(self):
        """Basic calculation check."""
        x = [1, 2, 3, 4, 5]
        y = [2, 3, 4, 5, 6]
        # diffs: 1, 1, 1, 1, 1 -> mean 1, std 0 -> division by zero handled?
        # Let's use varying data
        x = [1, 2, 3]
        y = [2, 4, 6] # diffs: 1, 2, 3 -> mean 2, std ~0.816
        # d = 2 / 0.816 ≈ 2.45

        d = calculate_cohens_d(x, y)
        assert d > 2.0
        assert d < 3.0

    def test_cohens_d_zero_variance(self):
        """Handle case where difference variance is zero."""
        x = [1, 1, 1]
        y = [2, 2, 2] # diffs: 1, 1, 1 -> std 0
        
        # The function should handle this gracefully (return inf or 0)
        # Our implementation returns 0.0 if std is 0 to avoid division by zero
        d = calculate_cohens_d(x, y)
        assert d == 0.0 or math.isinf(d)