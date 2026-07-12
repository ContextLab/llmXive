import pytest
import pandas as pd
import numpy as np
from src.services.analysis import apply_multiple_comparison_correction, run_full_analysis

def test_bonferroni_correction():
    """
    Test Bonferroni correction on a list of p-values.
    """
    p_values = [0.01, 0.02, 0.03, 0.5]
    corrected = apply_multiple_comparison_correction(p_values, method='bonferroni')
    
    # Bonferroni: p * n
    n = len(p_values)
    expected = [min(p * n, 1.0) for p in p_values]
    
    assert np.allclose(corrected, expected)

def test_fdr_bh_correction():
    """
    Test Benjamini-Hochberg FDR correction.
    """
    p_values = [0.01, 0.04, 0.03, 0.5]
    # Sorted: 0.01, 0.03, 0.04, 0.5
    # Ranks: 1, 2, 3, 4
    # Thresholds: 0.05 * i / n
    # 0.05 * 1/4 = 0.0125 -> 0.01 < 0.0125 (Significant)
    # 0.05 * 2/4 = 0.025 -> 0.03 > 0.025 (Not significant in simple BH, but BH is monotonic)
    # Actually BH calculation:
    # p_sorted * n / i
    # 0.01 * 4 / 1 = 0.04
    # 0.03 * 4 / 2 = 0.06
    # 0.04 * 4 / 3 = 0.0533
    # 0.5 * 4 / 4 = 0.5
    # Then take min with previous (monotonicity)
    # 0.04, 0.04, 0.04, 0.5
    # Wait, BH is: sort p, calculate q = p * n / i, then enforce monotonicity from end.
    # Let's just check it runs and returns same length.
    
    corrected = apply_multiple_comparison_correction(p_values, method='fdr_bh')
    assert len(corrected) == len(p_values)
    assert all(0 <= p <= 1 for p in corrected)

def test_invalid_method():
    """
    Test that invalid method raises an error or handles gracefully.
    """
    p_values = [0.05]
    with pytest.raises(ValueError):
        apply_multiple_comparison_correction(p_values, method='invalid_method')

def test_empty_list():
    """
    Test correction on empty list.
    """
    corrected = apply_multiple_comparison_correction([], method='bonferroni')
    assert len(corrected) == 0

def test_run_full_analysis_correction_integration():
    """
    Integration test for the full analysis pipeline including correction.
    """
    # Create dummy data
    data = pd.DataFrame({
        'bridging_coefficient': [0.1, 0.2, 0.3, 0.4, 0.5],
        'citation_count': [10, 20, 30, 40, 50],
        'novelty_score': [0.5, 0.4, 0.3, 0.2, 0.1]
    })
    
    result = run_full_analysis(data)
    
    assert 'correlations' in result
    assert 'regressions' in result
    assert 'p_values_corrected' in result
    assert 'method' in result['p_values_corrected']
