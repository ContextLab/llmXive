"""
Tests for statistical analysis module.
"""
import pytest
import numpy as np
from code.statistical_analysis import (
    compute_effect_size_cohen_d,
    compute_power_cohen_d,
    compute_cliffs_delta,
    get_effect_size_magnitude,
    run_mann_whitney_u_test,
    apply_benjamini_hochberg_correction,
    run_benjamini_hochberg_correction_on_metrics
)

def test_compute_effect_size_cohen_d():
    """Test Cohen's d calculation."""
    group1 = np.array([1, 2, 3, 4, 5])
    group2 = np.array([2, 3, 4, 5, 6])
    
    d = compute_effect_size_cohen_d(group1, group2)
    assert isinstance(d, float)
    assert d < 0  # group1 < group2
    
    # Identical groups should give 0
    d_identical = compute_effect_size_cohen_d(group1, group1)
    assert abs(d_identical) < 1e-10

def test_compute_cliffs_delta():
    """Test Cliff's Delta calculation."""
    group1 = np.array([1, 2, 3])
    group2 = np.array([4, 5, 6])
    
    delta = compute_cliffs_delta(group1, group2)
    assert -1 <= delta <= 1
    assert delta < 0  # group1 values are smaller
    
    # Perfect separation
    group1_sep = np.array([1, 2])
    group2_sep = np.array([3, 4])
    delta_sep = compute_cliffs_delta(group1_sep, group2_sep)
    assert delta_sep < 0
    assert abs(delta_sep) > 0.5

def test_get_effect_size_magnitude():
    """Test effect size magnitude classification."""
    assert get_effect_size_magnitude(0.05) == "negligible"
    assert get_effect_size_magnitude(0.2) == "small"
    assert get_effect_size_magnitude(0.4) == "medium"
    assert get_effect_size_magnitude(0.6) == "large"
    
    # Negative values should use absolute value
    assert get_effect_size_magnitude(-0.2) == "small"

def test_run_mann_whitney_u_test():
    """Test Mann-Whitney U test."""
    group1 = np.array([1, 2, 3, 4, 5])
    group2 = np.array([6, 7, 8, 9, 10])
    
    stat, pval = run_mann_whitney_u_test(group1, group2)
    assert stat >= 0
    assert 0 <= pval <= 1
    
    # Identical groups should give high p-value
    _, pval_identical = run_mann_whitney_u_test(group1, group1)
    assert pval_identical > 0.5

def test_apply_benjamini_hochberg_correction():
    """Test Benjamini-Hochberg correction."""
    # Known p-values
    p_values = [0.01, 0.04, 0.03, 0.005, 0.02]
    adjusted = apply_benjamini_hochberg_correction(p_values)
    
    assert len(adjusted) == len(p_values)
    assert all(0 <= a <= 1 for a in adjusted)
    
    # Adjusted p-values should be >= raw p-values
    assert all(adj >= raw for adj, raw in zip(adjusted, p_values))
    
    # Test with all ones
    ones = [1.0, 1.0, 1.0]
    adj_ones = apply_benjamini_hochberg_correction(ones)
    assert all(a == 1.0 for a in adj_ones)

def test_run_benjamini_hochberg_correction_on_metrics():
    """Test BH correction on metric results dictionary."""
    raw_results = {
        'metric1': {'p_value_raw': 0.01, 'statistic': 10.0},
        'metric2': {'p_value_raw': 0.05, 'statistic': 15.0},
        'metric3': {'p_value_raw': 0.001, 'statistic': 20.0}
    }
    
    corrected = run_benjamini_hochberg_correction_on_metrics(raw_results)
    
    assert 'metric1' in corrected
    assert 'p_value_adjusted' in corrected['metric1']
    assert 'p_value_adjusted' in corrected['metric2']
    assert 'p_value_adjusted' in corrected['metric3']
    
    # Adjusted values should be >= raw values
    for metric in corrected:
        assert corrected[metric]['p_value_adjusted'] >= corrected[metric]['p_value_raw']

def test_empty_input_handling():
    """Test handling of empty inputs."""
    assert apply_benjamini_hochberg_correction([]) == []
    
    result = run_benjamini_hochberg_correction_on_metrics({})
    assert result == {}
    
    _, pval = run_mann_whitney_u_test(np.array([]), np.array([]))
    assert pval == 1.0

def test_nan_handling():
    """Test handling of NaN values in p-values."""
    p_values = [0.01, float('nan'), 0.05]
    adjusted = apply_benjamini_hochberg_correction(p_values)
    
    # Should handle gracefully (NaN excluded from calculation)
    assert len(adjusted) == 3
    # The NaN position should get a default value (1.0)
    assert adjusted[1] == 1.0

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
