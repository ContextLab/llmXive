import pytest
import math
from code.analysis import apply_bonferroni_correction

def test_bonferroni_single_test():
    """Test that a single p-value remains unchanged when no correction is needed."""
    p_values = [0.05]
    corrected = apply_bonferroni_correction(p_values)
    assert len(corrected) == 1
    assert math.isclose(corrected[0], 0.05, rel_tol=1e-9)

def test_bonferroni_multiple_tests():
    """Test Bonferroni correction logic for multiple hypotheses."""
    p_values = [0.01, 0.02, 0.04, 0.05]
    n_tests = len(p_values)
    corrected = apply_bonferroni_correction(p_values)
    
    expected = [p * n_tests for p in p_values]
    
    assert len(corrected) == len(expected)
    for c, e in zip(corrected, expected):
        assert math.isclose(c, e, rel_tol=1e-9)

def test_bonferroni_cap_at_one():
    """Test that corrected p-values are capped at 1.0."""
    p_values = [0.1, 0.2, 0.3]
    n_tests = len(p_values)
    corrected = apply_bonferroni_correction(p_values)
    
    for p in corrected:
        assert p <= 1.0
        assert p >= 0.0

def test_bonferroni_unchanged_small():
    """Test that very small p-values are corrected correctly."""
    p_values = [0.001, 0.002]
    n_tests = len(p_values)
    corrected = apply_bonferroni_correction(p_values)
    
    assert math.isclose(corrected[0], 0.002, rel_tol=1e-9)
    assert math.isclose(corrected[1], 0.004, rel_tol=1e-9)

def test_bonferroni_empty_list():
    """Test handling of an empty list of p-values."""
    p_values = []
    corrected = apply_bonferroni_correction(p_values)
    assert corrected == []

def test_bonferroni_significance_threshold():
    """Test that significance status is correctly determined after correction."""
    p_values = [0.001, 0.01, 0.02, 0.05]
    alpha = 0.05
    corrected = apply_bonferroni_correction(p_values)
    
    # n = 4, so threshold is 0.05/4 = 0.0125
    # 0.001 * 4 = 0.004 (sig)
    # 0.01 * 4 = 0.04 (not sig)
    # 0.02 * 4 = 0.08 (not sig)
    # 0.05 * 4 = 0.2 (not sig)
    
    assert corrected[0] <= alpha
    assert corrected[1] > alpha
    assert corrected[2] > alpha
    assert corrected[3] > alpha
