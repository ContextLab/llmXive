import pytest
import pandas as pd
import numpy as np
from statistical_analysis import (
    apply_multiple_comparison_correction,
    calculate_spearman_correlation,
    calculate_vif
)

def test_bonferroni_correction():
    """Test Bonferroni correction logic."""
    p_values = [0.01, 0.03, 0.04, 0.06]
    n = len(p_values)
    expected = [min(p * n, 1.0) for p in p_values]
    corrected = apply_multiple_comparison_correction(p_values, method='bonferroni')
    
    for i, val in enumerate(corrected):
        assert abs(val - expected[i]) < 1e-6, f"Bonferroni correction failed at index {i}"

def test_bh_correction():
    """Test Benjamini-Hochberg correction logic."""
    # Simple case: p-values that should be adjusted
    p_values = [0.01, 0.02, 0.03, 0.04]
    corrected = apply_multiple_comparison_correction(p_values, method='benjamini_hochberg')
    
    # BH corrected p-values should be monotonically increasing (after sorting)
    # and generally larger than raw p-values (except the smallest might stay same or increase)
    assert all(c >= p for c, p in zip(corrected, p_values)), "BH corrected p-values should be >= raw"
    assert all(c <= 1.0 for c in corrected), "Corrected p-values should be <= 1.0"

def test_bh_monotonicity():
    """Test that BH correction enforces monotonicity."""
    # Construct a case where raw monotonicity might be violated after simple scaling
    # P-values: 0.01, 0.05, 0.02 (unsorted)
    # Sorted: 0.01, 0.02, 0.05
    # Ranks: 1, 2, 3
    # Adjusted: 0.01*3/1=0.03, 0.02*3/2=0.03, 0.05*3/3=0.05
    # Monotonicity check: 0.03, 0.03, 0.05 -> OK
    p_values = [0.01, 0.05, 0.02]
    corrected = apply_multiple_comparison_correction(p_values, method='benjamini_hochberg')
    
    # Check monotonicity in the sorted order
    sorted_indices = np.argsort(p_values)
    sorted_corrected = [corrected[i] for i in sorted_indices]
    
    for i in range(len(sorted_corrected) - 1):
        assert sorted_corrected[i] <= sorted_corrected[i+1], "BH corrected values must be monotonic"

def test_invalid_method():
    """Test that invalid method raises error."""
    with pytest.raises(ValueError):
        apply_multiple_comparison_correction([0.05], method='invalid_method')

def test_empty_list():
    """Test empty list returns empty list."""
    assert apply_multiple_comparison_correction([], method='bonferroni') == []

def test_single_pvalue():
    """Test single p-value correction."""
    p_values = [0.05]
    corrected_bonf = apply_multiple_comparison_correction(p_values, method='bonferroni')
    assert abs(corrected_bonf[0] - 0.05) < 1e-6
    
    corrected_bh = apply_multiple_comparison_correction(p_values, method='benjamini_hochberg')
    assert abs(corrected_bh[0] - 0.05) < 1e-6

def test_capping_at_one():
    """Test that corrected p-values are capped at 1.0."""
    p_values = [0.9, 0.95]
    corrected = apply_multiple_comparison_correction(p_values, method='bonferroni')
    assert all(c <= 1.0 for c in corrected)
    # 0.9 * 2 = 1.8 -> capped at 1.0
    assert corrected[0] == 1.0