import pytest
import numpy as np
from src.analysis.stats import (
    paired_ttest_heuristic_vs_fullbatch,
    check_stability,
    run_sensitivity_analysis,
    calculate_correlation_variance_error_pareto
)

class TestStabilityCheck:
    """Tests for the stability check function (T039)."""

    def test_perfect_stability(self):
        """When heuristic and fullbatch are identical, stability ratio should be 1.0."""
        h = [1.0, 2.0, 3.0, 4.0, 5.0]
        f = [1.0, 2.0, 3.0, 4.0, 5.0]
        
        result = check_stability(h, f, tolerance_lower=0.9, tolerance_upper=1.1, stability_threshold=0.95)
        
        assert result["is_stable"] is True
        assert result["stability_ratio"] == 1.0
        assert result["stable_count"] == 5
        assert result["total_count"] == 5
        assert len(result["outlier_indices"]) == 0

    def test_within_tolerance(self):
        """When ratios are within [0.9, 1.1], should be stable."""
        h = [0.95, 1.05, 0.91, 1.09, 1.0]
        f = [1.0, 1.0, 1.0, 1.0, 1.0]
        
        result = check_stability(h, f, tolerance_lower=0.9, tolerance_upper=1.1, stability_threshold=0.95)
        
        assert result["is_stable"] is True
        assert result["stability_ratio"] == 1.0
        assert len(result["outlier_indices"]) == 0

    def test_outside_tolerance(self):
        """When ratios exceed tolerance, should be unstable if below threshold."""
        # 4 out of 5 are stable (80%), threshold is 95% -> should be unstable
        h = [0.85, 0.95, 1.05, 1.0, 1.0] # 0.85 is < 0.9
        f = [1.0, 1.0, 1.0, 1.0, 1.0]
        
        result = check_stability(h, f, tolerance_lower=0.9, tolerance_upper=1.1, stability_threshold=0.95)
        
        assert result["is_stable"] is False
        assert result["stability_ratio"] == 0.8
        assert 0 in result["outlier_indices"]

    def test_zero_fullbatch_handling(self):
        """Handle case where fullbatch variance is zero."""
        h = [0.0, 0.0, 0.0]
        f = [0.0, 0.0, 0.0]
        
        result = check_stability(h, f)
        
        # 0/0 is treated as ratio 1.0 (perfect match)
        assert result["is_stable"] is True
        assert result["stability_ratio"] == 1.0

    def test_mixed_zero_handling(self):
        """Handle case where fullbatch is zero but heuristic is not."""
        h = [0.1, 0.0, 0.0]
        f = [0.0, 0.0, 0.0]
        
        result = check_stability(h, f)
        
        # First element: 0.1 / 0 -> inf (unstable)
        # Others: 0/0 -> 1.0 (stable)
        assert result["is_stable"] is False
        assert result["stable_count"] == 2
        assert result["total_count"] == 3
        assert 0 in result["outlier_indices"]

    def test_shape_mismatch_raises_error(self):
        """Should raise ValueError if shapes don't match."""
        h = [1.0, 2.0]
        f = [1.0, 2.0, 3.0]
        
        with pytest.raises(ValueError):
            check_stability(h, f)

    def test_empty_arrays(self):
        """Should handle empty arrays gracefully."""
        h = []
        f = []
        
        result = check_stability(h, f)
        
        assert result["is_stable"] is False
        assert result["stability_ratio"] == 0.0
        assert result["stable_count"] == 0
        assert result["total_count"] == 0
        assert len(result["outlier_indices"]) == 0

class TestPairedTTest:
    """Tests for the paired t-test function."""

    def test_identical_arrays(self):
        """If arrays are identical, p-value should be 1.0."""
        h = [1.0, 2.0, 3.0]
        f = [1.0, 2.0, 3.0]
        
        result = paired_ttest_heuristic_vs_fullbatch(h, f)
        
        assert np.isclose(result["p_value"], 1.0)
        assert result["mean_diff"] == 0.0

    def test_different_arrays(self):
        """If arrays are different, p-value should be low (significant difference)."""
        h = [1.0, 2.0, 3.0, 4.0, 5.0]
        f = [2.0, 3.0, 4.0, 5.0, 6.0]
        
        result = paired_ttest_heuristic_vs_fullbatch(h, f)
        
        assert result["mean_diff"] == -1.0
        # With perfect linear shift, t-stat should be significant
        assert result["p_value"] < 0.05

    def test_shape_mismatch(self):
        """Should raise ValueError if shapes don't match."""
        h = [1.0, 2.0]
        f = [1.0, 2.0, 3.0]
        
        with pytest.raises(ValueError):
            paired_ttest_heuristic_vs_fullbatch(h, f)

    def test_insufficient_samples(self):
        """Should raise ValueError if less than 2 samples."""
        h = [1.0]
        f = [1.0]
        
        with pytest.raises(ValueError):
            paired_ttest_heuristic_vs_fullbatch(h, f)

class TestSensitivityAnalysis:
    """Tests for sensitivity analysis function."""

    def test_sensitivity_analysis(self):
        """Run sensitivity analysis over different k values."""
        h_dict = {
            5: [0.9, 1.0, 1.1],
            10: [0.95, 1.05, 1.0],
            20: [0.99, 1.01, 1.0]
        }
        f_dict = {
            5: [1.0, 1.0, 1.0],
            10: [1.0, 1.0, 1.0],
            20: [1.0, 1.0, 1.0]
        }
        
        results = run_sensitivity_analysis(h_dict, f_dict)
        
        assert 5 in results
        assert 10 in results
        assert 20 in results
        assert results[5]["is_stable"] is True # All within 0.9-1.1

class TestCorrelationCalculation:
    """Tests for correlation calculation function."""

    def test_positive_correlation(self):
        """Test positive correlation detection."""
        errors = [1.0, 2.0, 3.0, 4.0, 5.0]
        distances = [1.1, 2.1, 3.1, 4.1, 5.1]
        
        result = calculate_correlation_variance_error_pareto(errors, distances)
        
        assert result["correlation_coefficient"] > 0.9
        assert result["p_value"] < 0.05

    def test_no_correlation(self):
        """Test no correlation detection."""
        errors = [1.0, 2.0, 3.0, 4.0, 5.0]
        # Random shuffle to break correlation
        distances = [5.0, 1.0, 4.0, 2.0, 3.0]
        
        result = calculate_correlation_variance_error_pareto(errors, distances)
        
        # Correlation should be low
        assert abs(result["correlation_coefficient"]) < 0.5

    def test_shape_mismatch(self):
        """Should raise ValueError if shapes don't match."""
        errors = [1.0, 2.0]
        distances = [1.0, 2.0, 3.0]
        
        with pytest.raises(ValueError):
            calculate_correlation_variance_error_pareto(errors, distances)

    def test_insufficient_samples(self):
        """Should raise ValueError if less than 2 samples."""
        errors = [1.0]
        distances = [1.0]
        
        with pytest.raises(ValueError):
            calculate_correlation_variance_error_pareto(errors, distances)
