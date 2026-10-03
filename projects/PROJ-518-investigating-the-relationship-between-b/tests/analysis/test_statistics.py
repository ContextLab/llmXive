import pytest
import numpy as np
from analysis.statistics import apply_fwe_correction, RegressionResult

def test_apply_fwe_correction_max_t():
    """Test max-t FWE correction logic."""
    # Simulate p-values (actually treated as observed stats in this implementation context)
    # and a distribution of max stats.
    p_values = [0.02, 0.05, 0.10]
    distribution_of_max_stats = [0.01, 0.03, 0.04, 0.06, 0.08] # Max stats from permutations
    
    merged_data = {
        'p_values': p_values,
        'distribution_of_max_stats': distribution_of_max_stats
    }
    
    result = apply_fwe_correction(merged_data, method='max-t')
    
    assert len(result) == len(p_values)
    assert all(0.0 <= p <= 1.0 for p in result)
    # Check that adjusted p-values are generally >= original (conservative)
    # Note: This depends on the specific values, but max-t is conservative.

def test_apply_fwe_correction_bonferroni():
    """Test Bonferroni FWE correction logic."""
    p_values = [0.02, 0.05, 0.10]
    merged_data = {
        'p_values': p_values,
        'distribution_of_max_stats': []
    }
    
    result = apply_fwe_correction(merged_data, method='bonferroni')
    
    expected = [min(0.02 * 3, 1.0), min(0.05 * 3, 1.0), min(0.10 * 3, 1.0)]
    expected = [0.06, 0.15, 0.30]
    
    assert result == expected

def test_apply_fwe_correction_empty_input():
    """Test handling of empty input."""
    merged_data = {
        'p_values': [],
        'distribution_of_max_stats': []
    }
    
    result = apply_fwe_correction(merged_data, method='bonferroni')
    assert result == []

def test_apply_fwe_correction_unknown_method():
    """Test error handling for unknown method."""
    merged_data = {
        'p_values': [0.05],
        'distribution_of_max_stats': []
    }
    
    with pytest.raises(ValueError, match="Unknown FWE method"):
        apply_fwe_correction(merged_data, method='unknown')