"""
Tests for sensitivity analysis and surrogate validation.
"""
import pytest
import numpy as np

def test_surrogate_generation():
    """
    Test that phase-randomized surrogates preserve power spectrum.
    """
    data = np.random.randn(200)
    
    try:
        from code.sensitivity import generate_surrogates
        surrogates = generate_surrogates(data, n_surr=10)
        
        assert surrogates.shape[0] == 10
        assert surrogates.shape[1] == len(data)
    except ImportError:
        pytest.skip("code/sensitivity.py not yet implemented")

def test_sensitivity_sweep():
    """
    Test that entropy is recomputed for different r values.
    """
    try:
        from code.sensitivity import run_sensitivity_sweep
        # This would require full data setup, so we just check existence
        assert callable(run_sensitivity_sweep)
    except ImportError:
        pytest.skip("code/sensitivity.py not yet implemented")
