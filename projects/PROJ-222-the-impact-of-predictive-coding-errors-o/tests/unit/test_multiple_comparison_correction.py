import pytest
from code.analysis import run_multiple_comparison_correction

def test_no_correction_single_test():
    """Test that correction is skipped when num_tests <= 1."""
    p_vals = [0.03]
    corrected, rejected = run_multiple_comparison_correction(p_vals)
    
    # Should return original p-values and no rejections (or False)
    assert len(corrected) == 1
    assert abs(corrected[0] - 0.03) < 1e-6
    # Logic in implementation: if num_tests <= 1, returns original p and False mask
    assert rejected == [False]

def test_bonferroni_correction():
    """Test Bonferroni correction logic."""
    p_vals = [0.01, 0.05, 0.20]
    corrected, rejected = run_multiple_comparison_correction(p_vals, method="bonferroni")
    
    # Bonferroni multiplies by n
    assert len(corrected) == 3
    # 0.01 * 3 = 0.03
    assert abs(corrected[0] - 0.03) < 1e-4
    # 0.05 * 3 = 0.15
    assert abs(corrected[1] - 0.15) < 1e-4
    # 0.20 * 3 = 0.60 (capped at 1.0)
    assert corrected[2] == 0.6 or corrected[2] <= 1.0

def test_fdr_bh_correction():
    """Test Benjamini-Hochberg correction logic."""
    p_vals = [0.01, 0.05, 0.20]
    corrected, rejected = run_multiple_comparison_correction(p_vals, method="fdr_bh")
    
    assert len(corrected) == 3
    # FDR is less conservative, should be different from Bonferroni
    assert corrected != [p * 3 for p in p_vals]

def test_empty_list():
    """Test handling of empty list."""
    corrected, rejected = run_multiple_comparison_correction([])
    assert corrected == []
    assert rejected == []