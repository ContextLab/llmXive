import pytest
import numpy as np
from analysis.statistics import apply_fwe_correction, merge_permutation_data
from errors import DataMissingCreativityError

def test_apply_fwe_correction_bonferroni():
    """Test Bonferroni FWE correction."""
    merged_data = {
        'p_values': [0.01, 0.03, 0.05],
        'distribution_of_max_stats': []  # Not used for Bonferroni
    }
    
    adjusted = apply_fwe_correction(merged_data, method='bonferroni')
    
    # Bonferroni: p * k, capped at 1.0
    expected = [0.03, 0.09, 0.15]
    assert adjusted == expected

def test_apply_fwe_correction_max_t():
    """Test max-t FWE correction."""
    # Create a distribution where some values are high
    distribution = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]
    merged_data = {
        'p_values': [0.05, 0.10, 0.15],
        'distribution_of_max_stats': distribution
    }
    
    adjusted = apply_fwe_correction(merged_data, method='max-t')
    
    # Should return list of adjusted p-values
    assert len(adjusted) == 3
    assert all(0 <= p <= 1 for p in adjusted)

def test_apply_fwe_correction_missing_data():
    """Test that missing data raises ValueError."""
    with pytest.raises(ValueError):
        apply_fwe_correction({'p_values': [0.05]}, method='max-t')
    
    with pytest.raises(ValueError):
        apply_fwe_correction({'distribution_of_max_stats': [0.1, 0.2]}, method='max-t')

def test_merge_permutation_data():
    """Test merging permutation data."""
    p_values = [0.01, 0.02, 0.03]
    distribution = [0.1, 0.2, 0.3]
    
    result = merge_permutation_data(p_values, distribution)
    
    assert result['p_values'] == p_values
    assert result['distribution_of_max_stats'] == distribution

def test_apply_fwe_correction_invalid_method():
    """Test that invalid method raises ValueError."""
    merged_data = {
        'p_values': [0.05],
        'distribution_of_max_stats': [0.1]
    }
    
    with pytest.raises(ValueError, match="Unknown FWE correction method"):
        apply_fwe_correction(merged_data, method='invalid_method')