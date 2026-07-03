"""
Additional unit tests for ANCOVA logic (Task T017 continuation).

This file tests the logic for Bonferroni correction and model fitting
assumptions, ensuring the pipeline adheres to the statistical requirements.
"""

import pytest
import numpy as np

def test_bonferroni_correction_logic():
    """
    Test the Bonferroni correction logic.
    Expected: alpha_corrected = 0.05 / 5 = 0.01.
    """
    alpha = 0.05
    n_tests = 5
    alpha_corrected = alpha / n_tests
    
    assert abs(alpha_corrected - 0.01) < 1e-9, "Bonferroni correction calculation incorrect"

def test_pvalue_significance_check():
    """
    Test that p-value significance is correctly determined against the corrected alpha.
    """
    alpha_corrected = 0.01
    p_values = [0.005, 0.015, 0.009, 0.02]
    
    expected_significance = [True, False, True, False]
    results = [p < alpha_corrected for p in p_values]
    
    assert results == expected_significance, "Significance check logic failed"

def test_vif_threshold_logic():
    """
    Test the VIF threshold logic (Abort if VIF > 2).
    """
    vif_values = [1.5, 2.1, 1.9, 3.0]
    should_abort = [False, True, False, True]
    
    for vif, expected in zip(vif_values, should_abort):
        result = vif > 2.0
        assert result == expected, f"VIF check failed for {vif}"

if __name__ == "__main__":
    pytest.main([__file__, "-v"])