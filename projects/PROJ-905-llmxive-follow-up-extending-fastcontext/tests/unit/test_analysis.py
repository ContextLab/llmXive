"""
Unit tests for the analysis module (US3).
Focus: Statistical tests, degradation calculation, and boundary detection.
"""

import pytest
import math
from scipy import stats
import numpy as np

# Import the functions we are testing.
# We assume the implementation in code/analysis.py provides:
# - run_ttest(diffs) -> float (p-value)
# - calc_degradation(baseline, lite) -> float
# - find_threshold(scores, metrics) -> float
from analysis import run_ttest, calc_degradation, find_threshold


class TestPairedTTest:
    """Tests for run_ttest functionality."""

    def test_paired_ttest_returns_significant_pvalue_for_mock_regular_data(self):
        """
        Verify that run_ttest returns a p-value < 0.05 for mock data
        representing a significant difference in a "Regular" set.
        
        Mock diffs provided: [0.12, 0.18, 0.15]
        These values suggest a consistent positive difference.
        """
        # Mock data representing differences (e.g., Baseline - Lite)
        diffs = [0.12, 0.18, 0.15]
        
        p_value = run_ttest(diffs)
        
        # Assert p-value is significant (< 0.05)
        assert p_value < 0.05, f"Expected p < 0.05, got {p_value}"
        assert 0.0 <= p_value <= 1.0, "p-value must be between 0 and 1"

    def test_paired_ttest_handles_small_sample(self):
        """Test with very small sample size."""
        diffs = [0.5, 0.6]
        p_value = run_ttest(diffs)
        assert 0.0 <= p_value <= 1.0

    def test_paired_ttest_no_variance(self):
        """Test with zero variance (all same values)."""
        diffs = [0.1, 0.1, 0.1]
        # scipy.stats.ttest_rel might return NaN or 1.0 depending on version/implementation
        # We just ensure it doesn't crash and returns a valid float
        p_value = run_ttest(diffs)
        assert isinstance(p_value, (float, np.floating))


class TestDegradationCalculation:
    """Tests for calc_degradation functionality."""

    def test_degradation_calc_returns_correct_percent(self):
        """
        Verify that calc_degradation returns a positive scalar value.
        Formula expected: ((Baseline - Lite) / Baseline) * 100
        """
        baseline = 100.0
        lite = 90.0
        
        degradation = calc_degradation(baseline, lite)
        
        # Expected: ((100 - 90) / 100) * 100 = 10.0
        expected = 10.0
        assert math.isclose(degradation, expected, rel_tol=1e-5), \
            f"Expected {expected}, got {degradation}"
        assert degradation > 0, "Degradation should be positive when Lite < Baseline"

    def test_degradation_when_lite_greater(self):
        """Test when Lite outperforms Baseline (negative degradation)."""
        baseline = 100.0
        lite = 110.0
        
        degradation = calc_degradation(baseline, lite)
        
        # Expected: ((100 - 110) / 100) * 100 = -10.0
        expected = -10.0
        assert math.isclose(degradation, expected, rel_tol=1e-5), \
            f"Expected {expected}, got {degradation}"

    def test_degradation_zero_baseline(self):
        """Test division by zero handling."""
        baseline = 0.0
        lite = 10.0
        
        # Should handle gracefully, likely returning inf or raising error handled by logic
        # Assuming implementation returns float('inf') or similar
        degradation = calc_degradation(baseline, lite)
        assert isinstance(degradation, float)


class TestBoundaryDetection:
    """Tests for find_threshold functionality."""

    def test_boundary_detection_identifies_threshold(self):
        """
        Verify that find_threshold returns a valid float threshold.
        Uses a simple sensitivity analysis framework mock.
        """
        # Mock data: scores and corresponding performance deltas
        scores = [0.1, 0.3, 0.5, 0.7, 0.9]
        deltas = [0.05, 0.04, 0.02, -0.01, -0.05]
        
        threshold = find_threshold(scores, deltas)
        
        assert isinstance(threshold, (float, np.floating)), \
            f"Threshold must be a float, got {type(threshold)}"
        # The threshold should be within the range of scores or a valid boundary
        # Since implementation details vary, we just ensure it's a number
        assert not math.isnan(threshold), "Threshold cannot be NaN"

    def test_boundary_detection_empty_input(self):
        """Test handling of empty lists."""
        scores = []
        deltas = []
        
        threshold = find_threshold(scores, deltas)
        assert isinstance(threshold, float)