import pytest
import numpy as np
from scipy import signal
from code.analysis.neff import calculate_neff
from code.analysis.correlation import ALPHA_ADJ, TOTAL_TESTS
from code.config import ACE_VARS, NOAA_VARS

def test_correlation_bonferroni_divisor():
    """
    T018: Unit test for Bonferroni correction divisor.
    Verify alpha_adj = 0.05 / 30.
    """
    # Expected values
    expected_params = len(ACE_VARS) # 3
    expected_indices = len(NOAA_VARS) # 2
    expected_lags = 5 # 0, 1, 2, 3, 6
    expected_total = expected_params * expected_indices * expected_lags # 30
    
    assert expected_total == 30, f"Expected total tests to be 30, got {expected_total}"
    assert TOTAL_TESTS == 30, f"TOTAL_TESTS constant mismatch: {TOTAL_TESTS}"
    
    expected_alpha_adj = 0.05 / 30
    assert abs(ALPHA_ADJ - expected_alpha_adj) < 1e-10, \
        f"ALPHA_ADJ mismatch: expected {expected_alpha_adj}, got {ALPHA_ADJ}"
    
    # Verify the calculation logic in the module matches the requirement
    # "derive the divisor 30 dynamically from configuration (3 params x 2 indices x 5 lags)"
    assert TOTAL_TESTS == len(ACE_VARS) * len(NOAA_VARS) * 5

def test_correlation_neff_formula():
    """
    T017: Unit test for Neff calculation.
    Verify formula: Neff = N * (1 - rho_1) / (1 + rho_1)
    """
    # Generate synthetic data with known autocorrelation
    # We use a random state for reproducibility
    rng = np.random.RandomState(42)
    N = 100
    data = rng.randn(N)
    
    # Detrend first (as per T021 requirement)
    detrended = signal.detrend(data)
    
    # Calculate lag-1 autocorrelation manually
    rho_1 = np.corrcoef(detrended[:-1], detrended[1:])[0, 1]
    
    # Calculate expected Neff
    if abs(1 + rho_1) < 1e-9:
        expected_neff = N
    else:
        expected_neff = N * (1 - rho_1) / (1 + rho_1)
    
    # Calculate using the function
    actual_neff = calculate_neff(data)
    
    # Allow for small floating point differences
    assert abs(actual_neff - expected_neff) < 1e-5, \
        f"Neff mismatch: expected {expected_neff}, got {actual_neff}"
    
    # Test with a highly autocorrelated series (rho ~ 0.9)
    # Create AR(1) process
    phi = 0.9
    ar_data = np.zeros(N)
    ar_data[0] = rng.randn()
    for i in range(1, N):
        ar_data[i] = phi * ar_data[i-1] + rng.randn()
    
    detrended_ar = signal.detrend(ar_data)
    rho_1_ar = np.corrcoef(detrended_ar[:-1], detrended_ar[1:])[0, 1]
    
    if abs(1 + rho_1_ar) < 1e-9:
        expected_neff_ar = N
    else:
        expected_neff_ar = N * (1 - rho_1_ar) / (1 + rho_1_ar)
        
    actual_neff_ar = calculate_neff(ar_data)
    
    # For phi=0.9, Neff should be significantly reduced
    # N * (1-0.9)/(1+0.9) = N * 0.1/1.9 = N * 0.0526 ~ 5
    assert actual_neff_ar < N, "Neff should be less than N for positive autocorrelation"
    assert abs(actual_neff_ar - expected_neff_ar) < 1.0, \
        f"Neff for AR(1) mismatch: expected ~{expected_neff_ar}, got {actual_neff_ar}"